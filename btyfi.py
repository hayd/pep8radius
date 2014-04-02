from __future__ import print_function
import argparse
import autopep8
from itertools import takewhile
import re
from subprocess import check_output, STDOUT, CalledProcessError
import sys
from sys import exit

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


__version__ = version = '0.5a'


DEFAULT_IGNORE = 'E24'
DEFAULT_INDENT_SIZE = 4


def main():
    description = ("Tidy up (autopep8) only the lines in the files touched "
                   "in the git branch/commit.")
    epilog = ("Run before you do a commit to tidy, "
              "or against a previous commit or branch before merging.")
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)
    parser.add_argument('rev',
                        help='commit or name of branch to compare against',
                        nargs='?')

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument('--version',
                       help='print version number and exit',
                       action='store_true')
    parser.add_argument('-v', '--verbose', action='count', dest='verbose',
                        default=0,
                        help='print verbose messages; '
                        'multiple -v result in more verbose messages')
    parser.add_argument('-d', '--diff', action='store_true', dest='diff',
                        help='print the diff for the fixed source')
    parser.add_argument('--dry-run', action='store_true',
                        help="do not make the changes in place and print diff")
    parser.add_argument('-p', '--pep8-passes', metavar='n',
                        default=-1, type=int,
                        help='maximum number of additional pep8 passes '
                        '(default: infinite)')
    parser.add_argument('-a', '--aggressive', action='count', default=0,
                        help='enable non-whitespace changes; '
                        'multiple -a result in more aggressive changes')
    parser.add_argument('--experimental', action='store_true',
                        help='enable experimental fixes')
    parser.add_argument('--exclude', metavar='globs',
                        help='exclude file/directory names that match these '
                        'comma-separated globs')
    parser.add_argument('--list-fixes', action='store_true',
                        help='list codes for fixes; '
                        'used by --ignore and --select')
    parser.add_argument('--ignore', metavar='errors', default='',
                        help='do not fix these errors/warnings '
                        '(default: {0})'.format(DEFAULT_IGNORE))
    parser.add_argument('--select', metavar='errors', default='',
                        help='fix only these errors/warnings (e.g. E4,W)')
    parser.add_argument('--max-line-length', metavar='n', default=79, type=int,
                        help='set maximum allowed line length '
                        '(default: %(default)s)')
    parser.add_argument('--indent-size', default=DEFAULT_INDENT_SIZE,
                        type=int, metavar='n',
                        help='number of spaces per indent level '
                             '(default %(default)s)')
    args = parser.parse_args()

    # sanity check args (fro autopep8)
    if args.max_line_length <= 0:
        parser.error('--max-line-length must be greater than 0')

    if args.select:
        args.select = args.select.split(',')

    if args.ignore:
        args.ignore = args.ignore.split(',')
    elif not args.select:
        if args.aggressive:
            # Enable everything by default if aggressive.
            args.select = ['E', 'W']
        else:
            args.ignore = DEFAULT_IGNORE.split(',')

    if args.exclude:
        args.exclude = args.exclude.split(',')
    else:
        args.exclude = []

    # main
    if args.version:
        print(version)
        exit(0)

    try:
        r = Radius.new(rev=args.rev, options=args)
    except NotImplementedError as e:
        print(e.message)
        exit(1)
    except CalledProcessError as c:
        # cut off usage of git diff and exit
        output = c.output.splitlines()[0]
        print(output)
        exit(c.returncode)

    r.pep8radius()


class Radius:

    def __init__(self, rev=None, options=None):
        self.rev = rev if rev is not None else self.current_branch()
        self.options = options if options else autopep8.parse_args([''])
        self.verbose = self.options.verbose
        self.dry_run = self.options.dry_run
        self.diff = self.options.diff or self.options.dry_run

        # TODO parse autopep8 options properly (ensure allowable)
        if not self.options.exclude:
            self.options.exclude = []
        if not self.options.ignore:
            self.options.ignore = DEFAULT_IGNORE.split(',')

        self.options.verbose = max(0, self.options.verbose - 1)
        self.options.in_place = False
        self.options.diff = False
        self.filenames_diff = self.get_filenames_diff()

    @staticmethod
    def new(rev=None, options=None, vc=None):
        """
        Create subclass instance of Radius with correct version control

        e.g. RadiusGit if using git

        """
        if vc is None:
            vc = which_version_control()

        try:
            r = radii[vc]
        except KeyError:
            return NotImplementedError("Unknown version control system.")

        return r(rev=rev, options=options)

    def pep8radius(self):
        "Better than you found it. autopep8 the diff lines in each py file"
        n = len(self.filenames_diff)

        self.p('Applying autopep8 to touched lines in %s file(s).'
               % len(self.filenames_diff))

        i = total_lines_changed = 0
        pep8_diffs = []
        for i, file_name in enumerate(self.filenames_diff, start=1):
            self.p('%s/%s: %s: ' % (i, n, file_name), end='')
            self.p('', min_=2)

            p_diff = self.pep8radius_file(file_name)
            lines_changed = udiff_lines_changes(p_diff) if p_diff else 0
            total_lines_changed += lines_changed
            self.p('fixed %s lines.' % lines_changed, max_=1)

            if p_diff and self.diff:
                pep8_diffs.append(p_diff)

        if self.dry_run:
            self.p('pep8radius would fix %s lines in %s files.'
                   % (total_lines_changed, i))
        else:
            self.p('pep8radius fixed %s lines in %s files.'
                   % (total_lines_changed, i))

        if self.diff:
            for diff in pep8_diffs:
                print(diff)

    def pep8radius_file(self, file_name):
        "Apply autopep8 to the diff lines of file f"
        # Presumably if was going to raise would have at get_filenames_diff
        cmd = self.file_diff_cmd(file_name)
        diff = check_output(cmd).decode('utf-8')

        with open(file_name, 'r') as f:
            original = f.read()

        partial = original
        for start, end in self.line_numbers_from_file_diff(diff):
            partial = self.autopep8_line_range(partial, start, end)
            # import pdb; pdb.set_trace()
            self.p('.', end='', max_=1)
        self.p('', max_=1)
        fixed = partial

        if not self.options.dry_run:
            with open(file_name, 'w') as f:
                f.write(fixed)
        return autopep8.get_diff_text(original.splitlines(True),
                                      fixed.splitlines(True),
                                      file_name)

    def autopep8_line_range(self, f, start, end):
        "Apply autopep8 between start and end of file f"
        self.options.line_range = [start, end]
        return autopep8.fix_code(f,   self.options)

    def get_filenames_diff(self):
        "Get the py files which have been changed since rev"
        cmd = self.filenames_diff_cmd()

        # Note: This may raise a CalledProcessError
        diff_files_b = check_output(cmd, stderr=STDOUT)

        diff_files_u = diff_files_b.decode('utf-8')
        diff_files = self.parse_diff_filenames(diff_files_u)

        return [f for f in diff_files if f.endswith('.py')]

    def line_numbers_from_file_diff(self, diff):
        "Potentially this is vc specific (if not using udiff)"
        return line_numbers_from_file_udiff(diff)

    def p(self, something_to_print, end=None, min_=1, max_=99):
        if min_ <= self.verbose <= max_:
            print(something_to_print, end=end)
            sys.stdout.flush()


# #####   udiff parsing   #####
# #############################

def line_numbers_from_file_udiff(udiff):
    """
    Parse a udiff, return iterator of tuples of (start, end) line numbers.

    Note: returned in descending order (as autopep8 can +- lines)

    """
    chunks = re.split('\n@@[^\n]+\n', udiff)[1:]

    line_numbers = re.findall('(?<=[+])\d+(?=,\d+)', udiff)
    line_numbers = map(int, line_numbers)

    # Note: this is reversed as can modify number of lines
    for c, start in reversed(zip(chunks, line_numbers)):
        empty = [line.startswith(' ') for line in c.splitlines()]
        pre_padding = sum(1 for _ in takewhile(lambda b: b, empty))
        new_lines = sum(line.startswith('+') for line in c)
        yield (start + pre_padding, start + pre_padding + new_lines)


def udiff_lines_changes(u):
    """
    Count lines removed in udiff

    """
    removed_changes = re.findall('\n\-', u)
    return sum(len(removed_changes) for c in removed_changes)


# #####   vc specific   #####
# ###########################

class RadiusGit(Radius):

    def current_branch(self):
        output = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return output.strip().decode('utf-8')

    def file_diff_cmd(self, f):
        "Get diff for one file, f"
        return ['git', 'diff', self.rev, f]

    def filenames_diff_cmd(self):
        "Get the names of the py files in diff"
        return ['git', 'diff', self.rev, '--name-only']

    @staticmethod
    def parse_diff_filenames(diff_files):
        "Parse the output of filenames_diff_cmd"
        return diff_files.splitlines()


class RadiusHg(Radius):

    def current_branch(self):
        output = check_output(["hg", "id", "-b"])
        return output.strip().decode('utf-8')

    def file_diff_cmd(self, f):
        "Get diff for one file, f"
        return ['hg', 'diff', '-c', self.rev, f]

    def filenames_diff_cmd(self):
        "Get the names of the py files in diff"
        return ["hg", "diff", "--stat", "-c", self.rev]

    @staticmethod
    def parse_diff_filenames(diff_files):
        "Parse the output of filenames_diff_cmd"
        # TODO promote this to Radius ?
        return re.findall('(?<=[$| |\n]).*\.py', diff_files)


radii = {'git': RadiusGit, 'hg': RadiusHg}


def using_git():
    try:
        git_log = check_output(["git", "log"], stderr=STDOUT)
        return True
    except CalledProcessError:
        return False


def using_hg():
    try:
        hg_log = check_output(["hg", "log"], stderr=STDOUT)
        return True
    except CalledProcessError:
        return False


def which_version_control():
    """
    Try to see if they are using git or hg.
    return git, hg or raise NotImplementedError.

    """
    if using_git():
        return 'git'

    if using_hg():
        return 'hg'

    # Not supported (yet)
    raise NotImplementedError("Unknown version control system. "
                              "Ensure you're in the project directory.")


if __name__ == "__main__":
    main()
