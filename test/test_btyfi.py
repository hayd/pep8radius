from __future__ import absolute_import
from autopep8 import get_diff_text
from btyfi import Radius, RadiusGit, RadiusHg
import filecmp
from os import remove
from shutil import copyfile
from subprocess import check_output, CalledProcessError
from sys import version_info

if version_info < (2, 7):
    from unittest2 import main, SkipTest, TestCase
else:
    from unittest import main, SkipTest, TestCase


class TestRadius(TestCase):
    _files = ['bad_original.py']

    def __init__(self, *args, **kwargs):
        super(TestRadius, self).__init__(*args, **kwargs)
        self.using_vc = self.using_vc_or_init_vc()

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
        self.assert_(filecmp.cmp(bad, better), self.get_file_diff(bad, better))

        # Run again
        r.pep8radius()
        self.assert_(filecmp.cmp(bad, better), self.get_file_diff(bad, better))

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

    def using_vc_or_init_vc(self):
        try:
            check_output(["git", "init"])
            return True
        except OSError:
            return False
        except CalledProcessError:
            pass  # possible can return False here
        try:
            check_output(["git", "log"])
            return True
        except CalledProcessError:
            pass
        return False


class TestRadiusHg(TestRadius, MixinTests):
    vc = 'hg'

    def using_vc_or_init_vc(self):
        try:
            check_output(["hg", "init"])
            return True
        except OSError:
            return False
        except CalledProcessError:
            pass
        try:
            check_output(["hg", "log"])
            return True
        except CalledProcessError:
            pass
        return False

if __name__ == '__main__':
    main()
