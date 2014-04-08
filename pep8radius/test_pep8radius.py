from __future__ import absolute_import
import autopep8
from difflib import unified_diff
import os
from pep8radius.pep8radius import (Radius, RadiusGit, RadiusHg,
                                   check_output, parse_args,
                                   which_version_control,
                                   using_git, using_hg,
                                   version)
from shutil import rmtree
from subprocess import CalledProcessError, STDOUT
import sys

if sys.version_info < (2, 7):
    from unittest2 import main, SkipTest, TestCase
else:
    from unittest import main, SkipTest, TestCase

PEP8RADIUS = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          'pep8radius.py')

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


class TestRadiusNoVCS(TestCase):

    def __init__(self, *args, **kwargs):
        self.original_dir = os.getcwd()
        super(TestRadiusNoVCS, self).__init__(*args, **kwargs)

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

        self.assertFalse(using_hg())
        TestRadiusHg.create_repo()
        self.assertTrue(using_hg())

        # again, git is already seen before this
        self.assertTrue(using_git())

    def test_args(self):
        # TODO see that these are passes on (use a static method in Radius?)

        args = ['hello.py']
        us = parse_args(args)
        them = autopep8.parse_args(args)
        self.assertEqual(us.select, them.select)
        self.assertEqual(us.ignore, them.ignore)

        args = ['hello.py', '--select=E1,W1', '--ignore=W601', '--max-line-length', '120']
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
        version_ = check_output(['python', PEP8RADIUS, '--version'])
        version_ = version_.decode('utf-8').strip()
        self.assertEqual(version_, version)

    def test_list_fixes(self):
        fixes = check_output(['python', PEP8RADIUS, '--list-fixes'])
        afixes = check_output(['autopep8', '--list-fixes'])
        self.assertEqual(fixes, afixes)

    def test_bad_rev(self):
        self.assertRaises(CalledProcessError,
                          check_output,
                          ['python', PEP8RADIUS, 'random_junk_sha'])

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
        os.chdir(self.original_dir)
        return success

    def check(self, original, modified, expected,
              test_name='check', options=None,
              directory=TEMP_DIR):
        """Modify original to modified, and check that pep8radius
        turns this into expected."""
        os.chdir(directory)
        if not self.using_vc:
            raise SkipTest("%s not available" % self.vc)

        temp_file = os.path.join(TEMP_DIR, 'temp.py')

        if options is None:
            options = []
        options += ['--in-place']

        options = parse_args(options)

        with open(temp_file, 'w') as f:
            f.write(original)
        committed = self.successfully_commit_files([temp_file],
                                                   commit=test_name)

        with open(temp_file, 'w') as f:
            f.write(modified)

        # Run pep8radius
        r = Radius.new(vc=self.vc, options=options)
        r.pep8radius()

        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

        # Run pep8radius again, it *should* be that this doesn't do anything.
        r.pep8radius()

        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

    def assert_equal(self, result, expected, test_name):
        """like assertEqual but with a nice diff output if not equal"""
        self.assertEqual(result, expected,
                         self.diff(expected, result, test_name))

    # This is similar to autopep8's get_diff_text
    @staticmethod
    def diff(expected, result, file_name):
        """Return text of unified diff between old and new."""
        result, expected = result.splitlines(True), expected.splitlines(True)
        newline = '\n'
        diff = unified_diff(expected, result,
                            file_name + '/expected',
                            file_name + '/result',
                            lineterm=newline)
        text = newline
        for line in diff:
            text += line
            # Work around missing newline (http://bugs.python.org/issue2142).
            if not line.endswith(newline):
                text += newline + r'\ No newline at end of file' + newline
        return text


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
        self.check(original, modified, expected, 'test_one_line', directory=SUBTEMP_DIR)

    def test_with_docformatter(self):
        original = 'def poor_indenting():\n  """       Great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  """  Very great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  """  Very great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_with_docformatter',)

        expected = 'def poor_indenting():\n  """Very great function."""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected,
                   'test_with_docformatter', ['--docformatter'])


class TestRadiusGit(TestRadius, MixinTests):
    vc = 'git'

    @staticmethod
    def delete_repo():
        try:
            rmtree(os.path.join(TEMP_DIR, '.git'))
        except OSError:
            pass

    @staticmethod
    def create_repo():
        os.chdir(TEMP_DIR)
        try:
            check_output(["git", "init"], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit"):
        os.chdir(TEMP_DIR)
        try:
            check_output(["git", "add"] + file_names, stderr=STDOUT)
            check_output(["git", "commit", "-m", commit], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False


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
            check_output(["hg", "init"], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit"):
        os.chdir(TEMP_DIR)
        try:
            check_output(["hg", "add"] + file_names, stderr=STDOUT)
            check_output(["hg", "commit", "-m", commit], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False

if __name__ == '__main__':
    main()
