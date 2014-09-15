from __future__ import absolute_import, with_statement

from contextlib import contextmanager
import errno
import os
from shutil import rmtree
import sys

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

if sys.version_info < (2, 7):
    from unittest2 import main as test_main, SkipTest, TestCase
else:
    from unittest import main as test_main, SkipTest, TestCase


ROOT_DIR = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.insert(0, ROOT_DIR)
from pep8radius import (Radius,
                        shell_out,
                        main,
                        parse_args,
                        version)
from pep8radius.diff import line_numbers_from_file_udiff, get_diff
from pep8radius.shell import CalledProcessError
from pep8radius.vcs import (VersionControl, Git, Bzr, Hg,
                            using_git, using_hg, using_bzr)
PEP8RADIUS = os.path.join(ROOT_DIR, 'pep8radius', '__init__.py')

TEMP_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'temp')
SUBTEMP_DIR = os.path.join(TEMP_DIR, 'subtemp')


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

@contextmanager
def from_dir(cwd):
    curdir = os.getcwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(curdir)

def pep8radius_main(args, vc=None):
    if isinstance(args, list):
        args = parse_args(args)
    with captured_output() as (out, err):
        try:
            main(args, vc=vc)
        except SystemExit:
            pass
    return out.getvalue().strip()


class MixinVcs(object):
    @classmethod
    def _save_and_commit(cls, contents, f):
        cls._save(contents, f)
        return cls.successfully_commit_files([f])

class MixinGit(MixinVcs):

    @staticmethod
    def delete_repo():
        try:
            temp_path = os.path.join(TEMP_DIR, '.git')
            rmtree(temp_path)
        except OSError as e: # pragma: no cover
        # see http://stackoverflow.com/questions/1213706/what-user-do-python-scripts-run-as-in-windows and http://stackoverflow.com/questions/7228296/permission-change-of-files-in-python
            if e.errno == errno.EACCES:
                import stat
                for dirpath, dirnames, filenames in os.walk(temp_path):
                    for filename in filenames:
                        os.chmod(os.path.join(dirpath, filename),
                                 stat.S_IWRITE)
                rmtree(temp_path)

    @staticmethod
    def create_repo():
        os.chdir(TEMP_DIR)
        try:
            shell_out(["git", "init"], cwd=TEMP_DIR)
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit",
                                  cwd=TEMP_DIR):
        os.chdir(TEMP_DIR)
        try:
            shell_out(["git", "add"] + file_names, cwd=cwd)
            shell_out(["git", "commit", "-m", commit], cwd=cwd)
            with from_dir(cwd):
                return Git().current_branch()
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def checkout(branch, create=False, cwd=TEMP_DIR):
        os.chdir(TEMP_DIR)
        if create:
            shell_out(["git", "checkout", '-b', branch], cwd=cwd)
        else:
            shell_out(["git", "checkout", branch], cwd=cwd)


class MixinHg(MixinVcs):

    @staticmethod
    def delete_repo():
        try:
            rmtree(os.path.join(TEMP_DIR, '.hg'))
        except OSError:
            pass

    @staticmethod
    def create_repo():
        os.chdir(TEMP_DIR)
        try:
            shell_out(["hg", "init"])
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit",
                                  cwd=TEMP_DIR):
        try:
            shell_out(["hg", "add"] + file_names, cwd=cwd)
            shell_out(["hg", "commit", "-m", commit], cwd=cwd)
            with from_dir(cwd):
                return Hg().current_branch()
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def checkout(branch, create=False, cwd=TEMP_DIR):
        os.chdir(TEMP_DIR)
        if create:
            shell_out(["hg", "branch", branch], cwd=cwd)
        else:
            shell_out(["hg", "update", "--check", branch], cwd=cwd)


class MixinBzr(MixinVcs):

    @staticmethod
    def delete_repo():
        try:
            rmtree(os.path.join(TEMP_DIR, '.bzr'))
        except OSError:
            pass

    @staticmethod
    def create_repo(cwd=TEMP_DIR):
        try:
            shell_out(["bzr", "init"], cwd=cwd)
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit",
                                  cwd=TEMP_DIR):
        try:
            shell_out(["bzr", "add"] + file_names, cwd=cwd)
            shell_out(["bzr", "commit", "-m", commit], cwd=cwd)
            with from_dir(cwd):
                return Bzr().current_branch()
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def checkout(branch, create=False, cwd=TEMP_DIR):
        create = ['--create-branch'] if create else []
        shell_out(["bzr", "switch", branch] + create, cwd=cwd)
