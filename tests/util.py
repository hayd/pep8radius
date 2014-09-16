from __future__ import with_statement

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
                        parse_args,
                        version)
from pep8radius.diff import modified_lines_from_udiff, get_diff
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
            from pep8radius.main import main
            main(args, vc=vc)
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


def save(contents, f):
    with from_dir(TEMP_DIR):
        with open(f, 'w') as f1:
            f1.write(contents)
