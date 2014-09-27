"""Everythin' you'll ever need in the tests..."""

from __future__ import with_statement

from contextlib import contextmanager
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
                        parse_args,
                        version)
from pep8radius.diff import modified_lines_from_udiff, get_diff
from pep8radius.shell import CalledProcessError, from_dir
from pep8radius.vcs import (VersionControl, Git, Bzr, Hg,
                            using_git, using_hg, using_bzr)


PEP8RADIUS = os.path.join(ROOT_DIR, 'pep8radius', '__init__.py')
TEST_DIR = os.path.abspath(os.path.dirname(__file__))
TEMP_DIR = os.path.join(TEST_DIR, 'temp')
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


def pep8radius_main(args, vc=None, cwd=TEMP_DIR, apply_config=False):
    with from_dir(cwd):
        with captured_output() as (out, err):
            try:
                from pep8radius.main import main
                main(args, vc=vc, apply_config=apply_config, cwd=cwd)
            except SystemExit:
                pass
        return out.getvalue().strip()


def mk_temp_dirs():
    try:
        os.mkdir(TEMP_DIR)
    except OSError:
        pass

    try:
        os.mkdir(SUBTEMP_DIR)
    except OSError:
        pass


def save(contents, f, cwd=TEMP_DIR):
    with from_dir(cwd):
        with open(f, 'w') as f1:
            f1.write(contents)


def remove(filename):
    """Delete file filename and don't raise if missing."""
    try:
        os.remove(filename)
    except OSError:
        pass


def remove_dir(directory):
    """Delete directory and all contained files and subdirectories.

    Note: this is the same as the shutil's rmtree function but overcomes
    a reported issue on Windows*.

    *Due to permissions (being able to create but not remove files).

    """
    try:
        rmtree(directory)
    except OSError as e:  # pragma: no cover
        # see http://stackoverflow.com/questions/1213706/
        # and http://stackoverflow.com/questions/7228296/
        from errno import EACCES
        if e.errno == EACCES:
            from stat import S_IWRITE
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    os.chmod(os.path.join(dirpath, filename), S_IWRITE)
            rmtree(directory)


def get_diff_many(modified, expected, files):
    return ''.join(get_diff(*mef)
                   for mef in zip(modified, expected, files))
