from __future__ import print_function
import argparse
import autopep8
import colorama
import docformatter
from difflib import unified_diff
from itertools import takewhile
import glob
import os
import re
import signal
import subprocess
from subprocess import STDOUT, CalledProcessError
import sys


# python 2.6 doesn't include check_output
if "check_output" not in dir(subprocess):  # pragma: no cover
    # duck punch it in!
    import subprocess

    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:  # pragma: no cover
            raise ValueError('stdout argument not allowed, '
                             'it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE,
                                   *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd,
                                                output=output)
        return output
    subprocess.check_output = check_output

    class CalledProcessError(Exception):

        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output

        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (
                self.cmd, self.returncode)
    # overwrite CalledProcessError due to `output`
    # keyword not being available (in 2.6)
    subprocess.CalledProcessError = CalledProcessError
check_output = subprocess.check_output


__version__ = version = '0.8.1'


DEFAULT_IGNORE = 'E24'
DEFAULT_INDENT_SIZE = 4


def main(args=None):
    try:  # pragma: no cover
        # Exit on broken pipe.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:  # pragma: no cover
        # SIGPIPE is not available on Windows.
        pass

    if args is None:
        args = parse_args(sys.argv[1:])

    try:
        # main
        if args.version:
            print(version)
            sys.exit(0)

        if args.list_fixes:
            for code, description in sorted(autopep8.supported_fixes()):
                print('{code} - {description}'.format(
                    code=code, description=description))
            sys.exit(0)

        try:
            r = Radius.new(rev=args.rev, options=args)
        except NotImplementedError as e:  # pragma: no cover
            print(e)
            sys.exit(1)
        except CalledProcessError as c:  # pragma: no cover
            # cut off usage of git diff and exit
            output = c.output.splitlines()[0]
            print(output)
            sys.exit(c.returncode)

        r.pep8radius()

    except KeyboardInterrupt:  # pragma: no cover
        return 1


def parse_args(arguments=None):
    description = ("PEP8 clean only the parts of the files which you have "
                   "touched since the last commit, previous commit or "
                   "branch.")
    epilog = ("Run before you commit, or against a previous commit or "
              "branch before merging.")
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
                        help='print the diff of fixed source vs original')
    parser.add_argument('-i', '--in-place', action='store_true',
                        help="make the changes in place")
    parser.add_argument('-f', '--docformatter', action='store_true',
                        help='fix docstrings for PEP257 using docformatter')
    parser.add_argument('--no-color', action='store_true',
                        help='do not print diffs in color')

    # autopep8 options
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
    # docformatter options
    parser.add_argument('--no-blank', dest='post_description_blank',
                        action='store_false',
                        help='do not add blank line after description; '
                             'used by docformatter')
    parser.add_argument('--pre-summary-newline',
                        action='store_true',
                        help='add a newline before the summary of a '
                             'multi-line docstring; used by docformatter')
    parser.add_argument('--force-wrap', action='store_true',
                        help='force descriptions to be wrapped even if it may '
                             'result in a mess; used by docformatter')

    if arguments is None:
        arguments = []

    args = parser.parse_args(arguments)

    # sanity check args (from autopep8)
    if args.max_line_length <= 0:  # pragma: no cover
        parser.error('--max-line-length must be greater than 0')

    if args.select:
        args.select = args.select.split(',')

    if args.ignore:
        args.ignore = args.ignore.split(',')
    elif not args.select and args.aggressive:
        # Enable everything by default if aggressive.
        args.select = ['E', 'W']
    else:
        args.ignore = DEFAULT_IGNORE.split(',')

    if args.exclude:
        args.exclude = args.exclude.split(',')
    else:
        args.exclude = []

    return args


class Radius:

    def __init__(self, rev=None, options=None):
        # pep8radius specific options
        self.rev = self._branch_point(rev)
        self.options = options if options else parse_args([''])
        self.verbose = self.options.verbose
        self.in_place = self.options.in_place
        self.diff = self.options.diff
        self.color = not self.options.no_color

        # autopep8 specific options
        self.options.verbose = max(0, self.options.verbose - 1)
        self.options.in_place = False
        self.options.diff = False

        # Note: This may raise a CalledProcessError, if it does it means
        # that there's been an error with the version control command.
        self.filenames_diff = self.get_filenames_diff()

    @staticmethod
    def new(rev=None, options=None, vc=None):
        """Create subclass instance of Radius with correct version control

        e.g. RadiusGit if using git

        """
        if vc is None:
            # Note: this can raise a NotImplementedError if it exhausts
            # list of supported version controls without success.
            vc = which_version_control()

        try:
            r = radii[vc]
        except KeyError:
            raise NotImplementedError("Unknown version control system.")

        return r(rev=rev, options=options)

    def pep8radius(self):
        """PEP8 clean only the parts of the files which you have touched
        since the last commit, previous commit or branch.

        """
        n = len(self.filenames_diff)

        self.p('Applying autopep8 to touched lines in %s file(s).' % n)

        total_lines_changed = 0
        pep8_diffs = []
        for i, file_name in enumerate(self.filenames_diff, start=1):
            self.p('%s/%s: %s: ' % (i, n, file_name), end='')
            self.p('', min_=2)

            p_diff = self.pep8radius_file(file_name)
            lines_changed = udiff_lines_fixed(p_diff) if p_diff else 0
            total_lines_changed += lines_changed
            self.p('fixed %s lines.' % lines_changed, max_=1)

            if p_diff and self.diff:
                pep8_diffs.append(p_diff)

        if self.in_place:
            self.p('pep8radius fixed %s lines in %s files.'
                   % (total_lines_changed, n))
        else:
            self.p('pep8radius would fix %s lines in %s files.'
                   % (total_lines_changed, n))

        if self.diff:
            for diff in pep8_diffs:
                self.print_diff(diff, color=self.color)

    def pep8radius_file(self, file_name):
        """Apply autopep8 to the diff lines of a file.
        Returns the diff between original and fixed file.

        """
        # We hope that a CalledProcessError would have already raised
        # during the init if it were going to raise here.
        cmd = self.file_diff_cmd(file_name)
        diff = check_output(cmd).decode('utf-8')

        with open(file_name, 'r') as f:
            original = f.read()

        # Apply line fixes "up" the file (i.e. in reverse) so that
        # fixes do not affect changes we're yet to make.
        partial = original
        for start, end in self.line_numbers_from_file_diff(diff):
            partial = self.autopep8_line_range(partial, start, end)
            self.p('.', end='', max_=1)
        self.p('', max_=1)
        fixed = partial

        if self.in_place:
            with open(file_name, 'w') as f:
                f.write(fixed)
        return get_diff(original, fixed, file_name)

    def autopep8_line_range(self, f, start, end):
        """Apply autopep8 between start and end of file f xcasxz."""
        self.options.line_range = [start, end]
        fixed = autopep8.fix_code(f,   self.options)

        if self.options.docformatter:
            fixed = docformatter.format_code(
                fixed,
                summary_wrap_length=self.options.max_line_length - 1,
                description_wrap_length=(self.options.max_line_length
                                         - 2 * self.options.indent_size),
                pre_summary_newline=self.options.pre_summary_newline,
                post_description_blank=self.options.post_description_blank,
                force_wrap=self.options.force_wrap,
                line_range=[start, end])

        return fixed

    def get_filenames_diff(self):
        "Get the py files which have been changed since rev"
        cmd = self.filenames_diff_cmd()

        # Note: This may raise a CalledProcessError
        diff_files = check_output(cmd, stderr=STDOUT).decode('utf-8')
        diff_files = self.parse_diff_filenames(diff_files)

        py_files = set(f for f in diff_files if f.endswith('.py'))

        if self.options.exclude:
            # TODO do we have to take this from root dir?
            for pattern in self.options.exclude:
                py_files.difference_update(glob.fnmatch.filter(py_files,
                                                               pattern))

        root_dir = self.root_dir()
        py_files_full = [os.path.join(root_dir,
                                      file_name)
                         for file_name in py_files]

        return list(py_files_full)

    def line_numbers_from_file_diff(self, diff):
        "Potentially this is vc specific (if not using udiff)"
        for start, end in line_numbers_from_file_udiff(diff):
            yield start, end

    def p(self, something_to_print, end=None, min_=1, max_=99):
        if min_ <= self.verbose <= max_:
            print(something_to_print, end=end)
            sys.stdout.flush()

    def print_diff(self, diff, color=True):
        if not self.diff or not diff:
            return

        if not color:
            colorama.init = lambda autoreset: None
            colorama.Fore.RED = ''
            colorama.Back.RED = ''
            colorama.Fore.GREEN = ''
            colorama.deinit = lambda: None

        colorama.init(autoreset=True)  # TODO use context_manager
        for line in diff.splitlines():
            if line.startswith('+') and not line.startswith('+++ '):
                # Note there shouldn't be trailing whitespace
                # but may be nice to generalise this
                print(colorama.Fore.GREEN + line)
            elif line.startswith('-') and not line.startswith('--- '):
                split_whitespace = re.split('(\s+)$', line)
                if len(split_whitespace) > 1:  # claim it must be 3
                    line, trailing, _ = split_whitespace
                else:
                    line, trailing = split_whitespace[0], ''
                print(colorama.Fore.RED + line, end='')
                # give trailing whitespace a RED background
                print(colorama.Back.RED + trailing)
            elif line == '\ No newline at end of file':
                # The assumption here is that there is now a new line...
                print(colorama.Fore.RED + line)
            else:
                print(line)
        colorama.deinit()

    def _branch_point(self, rev=None):
        current = self.current_branch()
        if rev is None:
            return current
        else:
            return self.merge_base(rev, current)


# #####   udiff parsing   #####
# #############################

def line_numbers_from_file_udiff(udiff):
    """Parse a udiff, return iterator of tuples of (start, end) line numbers.

    Note: returned in descending order (as autopep8 can +- lines)

    """
    chunks = re.split('\n@@[^\n]+\n', udiff)[:0:-1]

    line_numbers = re.findall('(?<=[+])\d+(?=,\d+)', udiff)
    line_numbers = list(map(int, line_numbers))[::-1]

    # Note: these were reversed as can modify number of lines
    for c, start in zip(chunks, line_numbers):
        empty = [line.startswith(' ') for line in c.splitlines()]
        pre_padding = sum(1 for _ in takewhile(lambda b: b, empty))
        post_padding = sum(1 for _ in takewhile(lambda b: b, empty[::-1]))

        sub_lines = sum(line.startswith('-') for line in c.splitlines())
        lines_in_range = len(c.splitlines()) - sub_lines - post_padding
        # The lines_in_range are either added or remained the same between
        # the padding line, we could be slightly fussier and return only
        # the ranges of added lines, but chose not to.
        yield (start + pre_padding,
               start + lines_in_range - 1)


def udiff_lines_fixed(u):
    """Count lines fixed (removed) in udiff.

    """
    removed_changes = re.findall('\n\-', u)
    return len(removed_changes)


# This is similar to autopep8's get_diff_text
def get_diff(original, fixed, file_name,
             original_label='original', fixed_label='fixed'):
    """Return text of unified diff between original and fixed."""
    original, fixed = original.splitlines(True), fixed.splitlines(True)
    newline = '\n'
    diff = unified_diff(original, fixed,
                        os.path.join(file_name, original_label),
                        os.path.join(file_name, fixed_label),
                        lineterm=newline)
    text = ''
    for line in diff:
        text += line
        # Work around missing newline (http://bugs.python.org/issue2142).
        if not line.endswith(newline):
            text += newline + r'\ No newline at end of file' + newline
    return text


# #####   vc specific   #####
# ###########################

class RadiusGit(Radius):

    @staticmethod
    def current_branch():
        output = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return output.strip().decode('utf-8')

    @staticmethod
    def root_dir():
        output = check_output(['git', 'rev-parse', '--show-toplevel'])
        root = output.strip().decode('utf-8')
        return os.path.normpath(root)

    @staticmethod
    def merge_base(rev1, rev2):
        output = check_output(['git', 'merge-base', rev1, rev2])
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

    @staticmethod
    def current_branch():
        output = check_output(["hg", "id", "-b"])
        return output.strip().decode('utf-8')

    @staticmethod
    def root_dir():
        output = check_output(['hg', 'root'])
        return output.strip().decode('utf-8')

    @staticmethod
    def merge_base(rev1, rev2):
        output = check_output(['hg', 'debugancestor', rev1, rev2])
        return output.strip().decode('utf-8').split(':')[1]

    def file_diff_cmd(self, f):
        "Get diff for one file, f"
        return ['hg', 'diff', '-r', self.rev, f]

    def filenames_diff_cmd(self):
        "Get the names of the py files in diff"
        return ["hg", "diff", "--stat", "-r", self.rev]

    @staticmethod
    def parse_diff_filenames(diff_files):
        "Parse the output of filenames_diff_cmd"
        # one issue is that occasionaly you get stdout from something else
        # specifically I found this in Coverage.py, luckily the format is
        # different (at least in this case)
        it = re.findall('(\n|^) (?P<file_name>.*\.py) \|', diff_files)
        return [t[1] for t in it]


radii = {'git': RadiusGit, 'hg': RadiusHg}


def using_git():
    try:
        git_log = check_output(["git", "log"], stderr=STDOUT)
        return True
    except (CalledProcessError, OSError):  # pragma: no cover
        return False


def using_hg():
    try:
        hg_log = check_output(["hg",   "log"], stderr=STDOUT)
        return True
    except (CalledProcessError, OSError):
        return False


def which_version_control():  # pragma: no cover
    """Try to see if they are using git or hg.
    return git, hg or raise NotImplementedError.

    """
    if using_git():
        return 'git'

    if using_hg():
        return 'hg'

    # Not supported (yet)
    raise NotImplementedError("Unknown version control system. "
                              "Ensure you're in the project directory.")


if __name__ == "__main__":  # pragma: no cover
    main()
