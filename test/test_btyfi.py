from __future__ import absolute_import
from autopep8 import get_diff_text
from btyfi import Radius, RadiusGit, RadiusHg
import filecmp
import os
from os import remove
from shutil import copyfile, rmtree
from subprocess import check_output, CalledProcessError
from sys import version_info

if version_info < (2, 7):
    from unittest2 import main, skipIf, SkipTest, TestCase
else:
    from unittest import main, skipIf, SkipTest, TestCase


def _in_test_directory():
    "If not in this directory, version control won't work correctly."
    # TODO just move to dir then move back?
    head, test = os.path.split(os.getcwd())
    _, pep8radius = os.path.split(head)
    return test == 'test' and pep8radius == 'pep8radius'

@skipIf(not _in_test_directory, "Not in test directory.")
class TestRadius(TestCase):
    _files = ['bad_original.py']

    def __init__(self, *args, **kwargs):
        self.using_vc = self.init_vc()
        super(TestRadius, self).__init__(*args, **kwargs)

    def init_vc(self):
        self.delete_and_create_repo()
        return self.successfully_create_and_commit_files(self._files)

    def setUp(self):
        if not self.using_vc:
            raise SkipTest("%s not available" % self.vc)

        for f in self._files:
            copyfile(f, 'temp_' + f)

    def tearDown(self):
        for f in self._files:
            copyfile('temp_' + f, f)
            remove('temp_' + f)

    def check(self, bad, changed, better):
        "Modify bad to changed, and then btyfi and check it becomes better"
        copyfile(changed, bad)

        # run btyfi
        r = Radius.new(vc=self.vc)
        r.pep8radius()
        # compare output to desired
        self.assertTrue(filecmp.cmp(bad, better), self.get_file_diff(bad, better))

        # Run again
        r.pep8radius()
        self.assertTrue(filecmp.cmp(bad, better), self.get_file_diff(bad, better))

    @staticmethod
    def get_file_diff(a, b):
        with open(a) as aa:
            with open(b) as bb:
                return get_diff_text(aa.read().splitlines(True),
                                     bb.read().splitlines(True),
                                     'result')

class MixinTests:

    def test_one_line(self):
        self.check('bad_original.py',
                   'changed_one_line.py',
                   'better_one_line.py')


class TestRadiusGit(TestRadius, MixinTests):
    vc = 'git'

    # Critical that we're in correct directory.

    def delete_and_create_repo(self):
        try:
            rmtree(os.path.join(os.getcwd(), '.git'))
        except OSError:
            pass

    def successfully_create_and_commit_files(self, file_names):
        try:
            check_output(["git", "init"])
            check_output(["git", "add"] + file_names)
            check_output(["git", "commit", "-m", "initial_commit"])
            return True
        except (OSError, CalledProcessError):
            return False


class TestRadiusHg(TestRadius, MixinTests):
    vc = 'hg'

    # Critical that we're in correct directory.

    def delete_and_create_repo(self):
        try:
            rmtree(os.path.join(os.getcwd(), '.hg'))
        except OSError:
            pass

    def successfully_create_and_commit_files(self, file_names):
        try:
            check_output(["hg", "init"])
            check_output(["hg", "add"] + file_names)
            check_output(["hg", "commit", "-m", "initial_commit"])
            return True
        except (OSError, CalledProcessError):
            return False

if __name__ == '__main__':
    main()
