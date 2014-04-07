from difflib import unified_diff
import os
from pep8radius import Radius, RadiusGit, RadiusHg, check_output, parse_args
from shutil import rmtree
from subprocess import CalledProcessError, STDOUT
import sys

if sys.version_info < (2, 7):
    from unittest2 import main, SkipTest, TestCase
else:
    from unittest import main, SkipTest, TestCase

TEMP_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'temp')
try:
    os.mkdir(TEMP_DIR)
except OSError:
    pass


class TestRadius(TestCase):

    def __init__(self, *args, **kwargs):
        self.original_dir = os.getcwd()
        self.using_vc = self.init_vc()
        super(TestRadius, self).__init__(*args, **kwargs)

    def init_vc(self):
        os.chdir(TEMP_DIR)
        success = self.delete_and_create_repo()
        os.chdir(self.original_dir)
        return success

    def check(self, original, modified, expected, test_name='check', options=None):
        """Modify original to modified, and check that pep8radius
        turns this into expected."""
        os.chdir(TEMP_DIR)
        if not self.using_vc:
            raise SkipTest("%s not available" % self.vc)

        temp_file = 'temp.py'

        if options is None:
            options = []
        options = parse_args(options)

        with open(temp_file, 'w') as f:
            f.write(original)
        committed = self.successfully_commit_files([temp_file])

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

        os.chdir(self.original_dir)

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

    def delete_and_create_repo(self):
        try:
            rmtree(os.path.join(TEMP_DIR, '.git'))
        except OSError:
            pass
        try:
            check_output(["git", "init"], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False

    def successfully_commit_files(self, file_names,
                                  commit="initial_commit"):
        try:
            check_output(["git", "add"] + file_names, stderr=STDOUT)
            check_output(["git", "commit", "-m", commit], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False


class TestRadiusHg(TestRadius, MixinTests):
    vc = 'hg'

    def delete_and_create_repo(self):
        try:
            rmtree(os.path.join(TEMP_DIR, '.hg'))
        except OSError:
            pass
        try:
            check_output(["hg", "init"], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False

    def successfully_commit_files(self, file_names,
                                  commit="initial_commit"):
        try:
            check_output(["hg", "add"] + file_names, stderr=STDOUT)
            check_output(["hg", "commit", "-m", commit], stderr=STDOUT)
            return True
        except (OSError, CalledProcessError):
            return False

if __name__ == '__main__':
    main()
