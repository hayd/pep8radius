from __future__ import print_function
import argparse
import re
from subprocess import check_output, STDOUT, CalledProcessError
from sys import exit


def main():
    description = ("Tidy up (autopep8) only the lines in the files touched "
                   "in the git branch/commit.")
    epilog = ("Run before you do a commit to tidy, "
              "or against a branch before merging.")
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)
    parser.add_argument('rev',
                        help='commit or name of branch to compare against',
                        nargs='?')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-v', '--verbose',
                       help='print which files/lines are being pep8d',
                       action='store_true')
    group.add_argument('--version',
                       help='print version number and exit',
                       action='store_true')

    args = parser.parse_args()

    if args.version:
        print('0.4')
        exit(0)

    try:
        r = Radius.from_vc(rev=args.rev, verbose=args.verbose)
    except NotImplementedError as e:
        print(e.message)
        exit(1)
    except CalledProcessError as c:
        # cut off usage of git diff and exit
        output = c.output.splitlines()[0]
        print(output)
        exit(c.returncode)

    r.btyfi()


class Radius:

    def __init__(self, rev=None, verbose=False):
        self.verbose = verbose
        self.rev = rev if rev is not None else self.current_branch()
        self.filenames_diff = self.get_filenames_diff()

    @classmethod
    def from_vc(self, rev=None, verbose=False, vc=None):
        """
        Create subclass instance of Radius with correct version control

        e.g. RadiusGit

        """
        if vc is None:
            vc = self.which_version_control()

        radii = {'git': RadiusGit, 'hg': RadiusHg}
        try:
            r = radii[vc]
        except KeyError:
            return NotImplementedError("Unknown version control system.")

        return r(rev=rev, verbose=verbose)

    def btyfi(self):
        "Better than you found it. autopep8 the diff lines in each py file"
        n = len(self.filenames_diff)

        self.p('Applying autopep8 to touched lines in %s file(s)'
               % len(self.filenames_diff))

        for i, f in enumerate(self.filenames_diff, start=1):
            self.p('%s/%s: Applying pep8radius to %s on lines:' % (i, n, f))
            self.pep8radius_file(f)

        self.p('Pep8radius complete, better than you found it!')

    def pep8radius_file(self, f):
        "Apply autopep8 to the diff lines of file f"
        # Presumably if was going to raise would have at get_filenames_diff
        cmd = self.file_diff_cmd(f)
        diff = check_output(cmd).decode('utf-8')

        self.p('     ', end='')
        for start, end in self.line_numbers_from_file_diff(diff):
            self.autopep8_line_range(f, start, end)
        self.p('')

    def autopep8_line_range(self, f, start, end):
        "Apply autopep8 between start and end of file f"
        self.p('%s-%s' % (end, start), end=', ')

        pep_log = check_output(['autopep8', '--in-place', '--range',
                                start, end, f])

    @classmethod
    def which_version_control(cls):
        """
        Try to see if they are using git or hg.
        return git, hg or raise NotImplementedError.

        """
        if cls.using_git():
            return 'git'

        if cls.using_hg():
            return 'hg'

        # Not supported (yet)
        raise NotImplementedError("Unknown version control system. "
                                  "Ensure you're in the project directory.")

    @staticmethod
    def using_git():
        try:
            git_log = check_output(["git", "log"], stderr=STDOUT)
            return True
        except CalledProcessError:
            return False

    @staticmethod
    def using_hg():
        try:
            hg_log = check_output(["hg", "log"], stderr=STDOUT)
            return True
        except CalledProcessError:
            return False

    def get_filenames_diff(self):
        "Get the py files which have been changed since rev"

        cmd = self.filenames_diff_cmd()

        # This may raise a CalledProcessError
        diff_files_b = check_output(cmd, stderr=STDOUT)

        diff_files_u = diff_files_b.decode('utf-8')
        diff_files = self.parse_diff_filenames(diff_files_u)

        # TODO ensure filter of py is done in filenames_diff_cmd
        return [f for f in diff_files if f.endswith('.py')]

    @classmethod
    def line_numbers_from_file_diff(cls, diff):
        """
        Parse a udiff, return iterator of tuples of (start, end) line numbers.

        Note: they are returned in descending order (autopep8 can +- lines)

        Potentially this needs to be overridden if not using udiff...

        """
        lines_with_line_numbers = [line for line in diff.splitlines()
                                   if line.startswith('@@')][::-1]
        # Note: we do this backwards, as autopep8 can add/remove lines

        for u in lines_with_line_numbers:
            start, end = map(str, cls.udiff_line_start_and_end(u))
            yield (start, end)

    @staticmethod
    def udiff_line_start_and_end(u):
        """
        Extract start line and end from udiff line

        Example
        -------
        '@@ -638,9 +638,17 @@ class GroupBy(PandasObject):'
        Returns the start line 638 and end line (638 + 17) (the lines added).

        """
        # I *think* we only care about the + lines?
        line_numbers = re.findall('(?<=[+])\d+,\d+', u)[0].split(',')
        line_numbers = list(map(int, line_numbers))

        PADDING_LINES = 3  # TODO perhaps this is configuarable?

        return (line_numbers[0] + PADDING_LINES,
                sum(line_numbers) - PADDING_LINES)

    def p(self, something_to_print, end=None):
        if self.verbose:
            print(something_to_print, end=end)


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
        #TODO promote this to Radius ?
        return re.findall('(?<=[$| |\n]).*\.py', diff_files)


if __name__ == "__main__":
    main()
