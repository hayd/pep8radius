"""This module defines the version control specific functionality, we need.

The aim is to work, for example to get the root directory, independent
of which version control system we are using. That is, subclasses of the
abstract class VersionControl are specific to vcs e.g. Git.

"""


import os
import re

from pep8radius.shell import (shell_out, shell_out_ignore_exitcode,
                              CalledProcessError)  # with 2.6 compat


class AbstractMethodError(NotImplementedError):
    pass


def using_git(cwd):
    """Test whether the directory cwd is contained in a git repository."""
    try:
        git_log = shell_out(["git", "log"], cwd=cwd)
        return True
    except (CalledProcessError, OSError):  # pragma: no cover
        return False


def using_hg(cwd):
    """Test whether the directory cwd is contained in a mercurial
    repository."""
    try:
        hg_log = shell_out(["hg",   "log"], cwd=cwd)
        return True
    except (CalledProcessError, OSError):
        return False


def using_bzr(cwd):
    """Test whether the directory cwd is contained in a bazaar repository."""
    try:
        bzr_log = shell_out(["bzr", "log"], cwd=cwd)
        return True
    except (CalledProcessError, OSError):
        return False


class VersionControl(object):

    """Abstract base class for defining the methods we need to work with a
    version control system."""

    def __init__(self, cwd=None):
        self.root = os.path.abspath(self.root_dir(cwd=cwd))

    def _shell_out(self, *args, **kwargs):
        return shell_out(*args, cwd=self.root, **kwargs)

    @staticmethod
    def from_string(vc):
        """Return the VersionControl superclass from a string, for example
        VersionControl.from_string('git') will return Git."""
        try:
            # Note: this means all version controls must have
            # a title naming convention (!)
            vc = globals()[vc.title()]
            assert(issubclass(vc, VersionControl))
            return vc
        except (KeyError, AssertionError):
            raise NotImplementedError("Unknown version control system.")

    @staticmethod
    def which(cwd=None):  # pragma: no cover
        """Try to find which version control system contains the cwd directory.

        Returns the VersionControl superclass e.g. Git, if none were
        found this will raise a NotImplementedError.

        """
        if cwd is None:
            cwd = os.getcwd()
        for (k, using_vc) in globals().items():
            if k.startswith('using_') and using_vc(cwd=cwd):
                return VersionControl.from_string(k[6:])

        # Not supported (yet)
        raise NotImplementedError("Unknown version control system, "
                                  "or you're not in the project directory.")

    # abstract methods
    @staticmethod
    def file_diff_cmd(r, file_name):  # pragma: no cover
        raise AbstractMethodError()

    @staticmethod
    def filenames_diff_cmd(r):  # pragma: no cover
        raise AbstractMethodError()

    @staticmethod
    def parse_diff_filenames(diff_files):  # pragma: no cover
        raise AbstractMethodError()

    @staticmethod
    def root_dir(cwd=None):  # pragma: no cover
        raise AbstractMethodError()

    def current_branch(self):  # pragma: no cover
        raise AbstractMethodError()

    @staticmethod
    def merge_base(rev1, rev2):  # pragma: no cover
        raise AbstractMethodError()

    def branch_point(self, rev=None):
        current = self.current_branch()
        if rev is None:
            return current
        else:
            return self.merge_base(rev, current)

    def modified_lines(self, r, file_name):
        """Returns the line numbers of a file which have been changed."""
        cmd = self.file_diff_cmd(r, file_name)
        diff = shell_out_ignore_exitcode(cmd, cwd=self.root)
        return list(self.modified_lines_from_diff(diff))

    def modified_lines_from_diff(self, diff):
        """Returns the changed lines in a diff.

        - Potentially this is vc specific (if not using udiff).

        Note: this returns the line numbers in descending order.

        """
        from pep8radius.diff import modified_lines_from_udiff
        for start, end in modified_lines_from_udiff(diff):
            yield start, end

    def get_filenames_diff(self, r):
        """Get the py files which have been changed since rev."""
        cmd = self.filenames_diff_cmd(r)

        diff_files = shell_out_ignore_exitcode(cmd, cwd=self.root)
        diff_files = self.parse_diff_filenames(diff_files)

        return set(f for f in diff_files if f.endswith('.py'))


class Git(VersionControl):

    def current_branch(self):
        return self._shell_out(["git", "rev-parse", "HEAD"])

    @staticmethod
    def root_dir(cwd=None):
        root = shell_out(['git', 'rev-parse', '--show-toplevel'], cwd=cwd)
        return os.path.normpath(root)

    def merge_base(self, rev1, rev2):
        return self._shell_out(['git', 'merge-base', rev1, rev2])

    @staticmethod
    def file_diff_cmd(r, f):
        """Get diff for one file, f."""
        return ['git', 'diff', r.rev, f]

    @staticmethod
    def filenames_diff_cmd(r):
        """Get the names of the py files in diff."""
        return ['git', 'diff', r.rev, '--name-only']

    @staticmethod
    def parse_diff_filenames(diff_files):
        """Parse the output of filenames_diff_cmd."""
        return diff_files.splitlines()


class Hg(VersionControl):

    def current_branch(self):
        return self._shell_out(["hg", "id"])[:12]  # this feels awkward

    @staticmethod
    def root_dir(cwd=None):
        return shell_out(['hg', 'root'], cwd=cwd)

    def merge_base(self, rev1, rev2):
        output = self._shell_out(['hg', 'debugancestor', rev1, rev2])
        return output.split(':')[1]

    @staticmethod
    def file_diff_cmd(r, f):
        """Get diff for one file, f."""
        return ['hg', 'diff', '-r', r.rev, f]

    @staticmethod
    def filenames_diff_cmd(r):
        """Get the names of the py files in diff."""
        return ["hg", "diff", "--stat", "-r", r.rev]

    @staticmethod
    def parse_diff_filenames(diff_files):
        """Parse the output of filenames_diff_cmd."""
        # one issue is that occasionaly you get stdout from something else
        # specifically I found this in Coverage.py, luckily the format is
        # different (at least in this case)
        it = re.findall('(\n|^) ?(?P<file_name>.*\.py)\s+\|', diff_files)
        return [t[1] for t in it]


class Bzr(VersionControl):

    def current_branch(self):
        return self._shell_out(["bzr", "version-info",
                                "--custom", "--template={revision_id}"])

    @staticmethod
    def root_dir(cwd=None):
        return shell_out(['bzr', 'root'], cwd=cwd)

    def merge_base(self, rev1, rev2):
        # Note: find-merge-base just returns rev1 if rev2 is not found
        # we assume that rev2 is a legitamate revision.
        # the following raise a CalledProcessError if it's a bad revision
        shell_out(['bzr', 'log', '-c', rev1], cwd=self.root)

        output = shell_out_ignore_exitcode(['bzr', 'find-merge-base',
                                            rev1, rev2],
                                           cwd=self.root)
        # 'merge base is revision name@example.com-20140602232408-d3wspoer3m35'
        return output.rsplit(' ', 1)[1]

    @staticmethod
    def file_diff_cmd(r, f):
        """Get diff for one file, f."""
        return ['bzr', 'diff', f, '-r', r.rev]

    @staticmethod
    def filenames_diff_cmd(r):
        """Get the names of the py files in diff."""
        # TODO Can we do this better (without parsing the entire diff?)
        return ['bzr', 'status', '-S', '-r', r.rev]  # TODO '--from-root' ?

    @staticmethod
    def parse_diff_filenames(diff_files):
        """Parse the output of filenames_diff_cmd."""
        # ?   .gitignore
        # M  0.txt
        files = []
        for line in diff_files.splitlines():
            line = line.strip()
            fn = re.findall('[^ ]+\s+(.*.py)', line)
            if fn and not line.startswith('?'):
                files.append(fn[0])
        return files
