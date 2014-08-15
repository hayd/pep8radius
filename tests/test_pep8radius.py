from __future__ import absolute_import
import autopep8
from contextlib import contextmanager
import os
from shutil import rmtree
import sys
import errno
import stat

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

if sys.version_info < (2, 7):
    from unittest2 import main, SkipTest, TestCase
else:
    from unittest import main, SkipTest, TestCase


ROOT_DIR = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.insert(0, ROOT_DIR)
from pep8radius import (Radius, RadiusGit, RadiusHg, RadiusBzr,
                        shell_out, CalledProcessError,
                        main,
                        parse_args,
                        which_version_control,
                        using_git, using_hg, using_bzr,
                        version, get_diff)

PEP8RADIUS = os.path.join(ROOT_DIR, 'pep8radius.py')

TEMP_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'temp')
SUBTEMP_DIR = os.path.join(TEMP_DIR, 'subtemp')
try:
    os.mkdir(TEMP_DIR)
except OSError:
    pass

try:
    os.mkdir(SUBTEMP_DIR)
except OSError:
    pass

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def pep8radius_main(args, vc=None):
    if isinstance(args, list):
        args = parse_args(args)
    with captured_output() as (out, err):
        try:
            main(args, vc=vc)
        except SystemExit:
            pass
    return out.getvalue().strip()


class TestRadiusNoVCS(TestCase):

    def __init__(self, *args, **kwargs):
        self.original_dir = os.getcwd()
        super(TestRadiusNoVCS, self).__init__(*args, **kwargs)

    def setUp(self):
        os.chdir(TEMP_DIR)

    def tearDown(self):
        os.chdir(self.original_dir)

    def test_no_vc(self):
        TestRadiusGit.delete_repo()
        TestRadiusHg.delete_repo()

        # self.assertRaises(NotImplementedError, which_version_control)
        # This see the above repo, which is pep8radius and using git !
        pass

    def test_bad_vc(self):
        self.assertRaises(NotImplementedError,
                          lambda x: Radius.new(vc=x),
                          'made_up_vc')

    def test_unknown_vc(self):
        # we have pep8radius is uing git...
        self.assertTrue(isinstance(Radius.new(None), RadiusGit))

    def test_using_vc(self):
        TestRadiusGit.delete_repo()
        TestRadiusHg.delete_repo()
        TestRadiusBzr.delete_repo()

        self.assertFalse(using_hg())
        if TestRadiusHg.create_repo():
            self.assertTrue(using_hg())

        self.assertFalse(using_bzr())
        if TestRadiusBzr.create_repo():
            self.assertTrue(using_bzr())

        # git is seen before this, as the dir above is git!
        self.assertTrue(using_git())

    def test_autopep8_args(self):
        # TODO see that these are passes on (use a static method in Radius?)

        args = ['hello.py']
        us = parse_args(args)
        them = autopep8.parse_args(args)
        self.assertEqual(us.select, them.select)
        self.assertEqual(us.ignore, them.ignore)

        args = ['hello.py', '--select=E1,W1', '--ignore=W601',
                '--max-line-length', '120']
        us = parse_args(args)
        them = autopep8.parse_args(args)
        self.assertEqual(us.select, them.select)
        self.assertEqual(us.ignore, them.ignore)
        self.assertEqual(us.max_line_length, them.max_line_length)

        args = ['hello.py', '--aggressive', '-v']
        us = parse_args(args)
        them = autopep8.parse_args(args)
        self.assertEqual(us.aggressive, them.aggressive)

    def test_version_number(self):
        version_ = pep8radius_main(['--version'])
        self.assertEqual(version_, version)

    def test_list_fixes(self):
        fixes = pep8radius_main(['--list-fixes'])
        afixes = shell_out(['autopep8', '--list-fixes'])
        self.assertEqual(fixes, afixes)


class TestRadius(TestCase):

    def __init__(self, *args, **kwargs):
        self.original_dir = os.getcwd()
        self.using_vc = self.init_vc()
        super(TestRadius, self).__init__(*args, **kwargs)

    def tearDown(self):
        os.chdir(self.original_dir)

    def init_vc(self):
        os.chdir(TEMP_DIR)
        self.delete_repo()
        success = self.create_repo()
        committed = self._save_and_commit('a=1;', 'a.py')
        os.chdir(self.original_dir)
        return success

    def setUp(self):
        os.chdir(TEMP_DIR)

    @classmethod
    def _save_and_commit(cls, contents, f):
        cls._save(contents, f)
        return cls.successfully_commit_files([f])

    @staticmethod
    def _save(contents, f):
        with open(f, 'w') as f1:
            f1.write(contents)

    @staticmethod
    def get_diff_many(modified, expected, files):
        return ''.join(get_diff(*mef)
                       for mef in zip(modified, expected, files))

    def check(self, original, modified, expected,
              test_name='check', options=None,
              directory=TEMP_DIR):
        """Modify original to modified, and check that pep8radius
        turns this into expected."""
        os.chdir(directory)
        if not self.using_vc:
            raise SkipTest("%s not available" % self.vc)

        temp_file = os.path.join(TEMP_DIR, 'temp.py')

        options = parse_args(options)

        # TODO remove this color hack, and actually test printing color diff
        options.no_color = True

        with open(temp_file, 'w') as f:
            f.write(original)
        committed = self.successfully_commit_files([temp_file],
                                                   commit=test_name)

        with open(temp_file, 'w') as f:
            f.write(modified)

        options.verbose = 1
        r = Radius.new(vc=self.vc, options=options)
        with captured_output() as (out, err):
            r.pep8radius()
        self.assertIn('would fix', out.getvalue())
        self.assertNotIn('@@', out.getvalue())
        options.verbose = 0

        options.diff = True
        r = Radius.new(vc=self.vc, options=options)
        with captured_output() as (out, err):
            r.pep8radius()
        exp_diff = get_diff(modified, expected, temp_file)
        self.assert_equal(out.getvalue(), exp_diff, test_name)
        options.diff = False

        options.in_place = True
        r = Radius.new(vc=self.vc, options=options)
        # Run pep8radius
        r.pep8radius()

        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

        # Run pep8radius again, it *should* be that this doesn't do anything.
        with captured_output() as (out, err):
            pep8radius_main(options, vc=self.vc)
        self.assertEqual(out.getvalue(), '')

        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

    def assert_equal(self, result, expected, test_name):
        """like assertEqual but with a nice diff output if not equal"""
        self.assertEqual(result, expected,
                         get_diff(expected, result, test_name,
                                  'expected', 'result'))


class MixinTests:

    """All Radius tests are placed in this class"""

    def test_one_line(self):
        original = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_one_line')

    def test_one_line_from_subdirectory(self):
        original = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_one_line',
                   directory=SUBTEMP_DIR)

    def test_with_docformatter(self):
        original = 'def poor_indenting():\n  """       Great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  """  Very great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  """  Very great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_without_docformatter')

        expected = 'def poor_indenting():\n  """Very great function."""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected,
                   'test_with_docformatter', ['--docformatter'])

    def test_bad_rev(self):
        os.chdir(TEMP_DIR)
        # TODO for some reason this isn't capturing the output!
        with captured_output() as (out, err):
            self.assertRaises(CalledProcessError,
                              lambda x: Radius.new(rev=x, vc=self.vc),
                              'random_junk_sha')
        os.chdir(self.original_dir)

    def test_earlier_revision(self):
        if self.vc == 'bzr':
            raise SkipTest()

        start = self._save_and_commit('a=1;', 'AAA.py')
        self.checkout('ter', create=True)
        self._save_and_commit('b=1;', 'BBB.py')
        tip = self._save_and_commit('c=1;', 'CCC.py')
        self._save('c=1', 'CCC.py')

        args = parse_args(['--diff', '--no-color'])
        r = Radius.new(rev=start, options=args, vc=self.vc)
        with captured_output() as (out, err):
            r.pep8radius()
        diff = out.getvalue()

        files = [os.path.join(TEMP_DIR, f) for f in ['BBB.py', 'CCC.py']]

        exp_diff = self.get_diff_many(['b=1;', 'c=1'],
                                      ['b = 1\n', 'c = 1\n'],
                                      files)
        self.assert_equal(diff, exp_diff, 'earlier_revision')

        # TODO test the diff is correct


class TestRadiusGit(TestRadius, MixinTests):
    vc = 'git'

    @staticmethod
    def delete_repo():
        try:
            temp_path = os.path.join(TEMP_DIR, '.git')
            rmtree(temp_path)
        except OSError as e:
        # see http://stackoverflow.com/questions/1213706/what-user-do-python-scripts-run-as-in-windows and http://stackoverflow.com/questions/7228296/permission-change-of-files-in-python
            if e.errno == errno.EACCES:
                for dirpath, dirnames, filenames in os.walk(temp_path):
                    for filename in filenames:
                        os.chmod(
                            os.path.join(dirpath, filename), stat.S_IWRITE)
                rmtree(temp_path)


    @staticmethod
    def create_repo():
        os.chdir(TEMP_DIR)
        try:
            shell_out(["git", "init"])
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit"):
        os.chdir(TEMP_DIR)
        try:
            shell_out(["git", "add"] + file_names)
            shell_out(["git", "commit", "-m", commit])
            return RadiusGit.current_branch()
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def checkout(branch, create=False):
        if create:
            shell_out(["git", "checkout", '-b', branch])
        else:
            shell_out(["git", "checkout", branch])


class TestRadiusHg(TestRadius, MixinTests):
    vc = 'hg'

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
                                  commit="initial_commit"):
        os.chdir(TEMP_DIR)
        try:
            shell_out(["hg", "add"] + file_names)
            shell_out(["hg", "commit", "-m", commit])
            return RadiusHg.current_branch()
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def checkout(branch, create=False):
        if create:
            shell_out(["hg", "branch", branch])
        else:
            shell_out(["hg", "update", "--check", branch])


class TestRadiusBzr(TestRadius, MixinTests):
    vc = 'bzr'

    @staticmethod
    def delete_repo():
        try:
            rmtree(os.path.join(TEMP_DIR, '.bzr'))
        except OSError:
            pass

    @staticmethod
    def create_repo():
        os.chdir(TEMP_DIR)
        try:
            shell_out(["bzr", "init"])
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit"):
        os.chdir(TEMP_DIR)
        try:
            shell_out(["bzr", "add"] + file_names)
            shell_out(["bzr", "commit", "-m", commit])
            return RadiusBzr.current_branch()
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def checkout(branch, create=False):
        create = ['--create-branch'] if create else []
        shell_out(["bzr", "switch", branch] + create)


if __name__ == '__main__':
    main()
