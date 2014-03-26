from __future__ import absolute_import
from btyfi import Radius, RadiusGit, RadiusHg
import filecmp
from os import remove
from unittest import TestCase
from shutil import copyfile
from subprocess import check_output

#ROOT_DIR = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

#sys.path.insert(0, ROOT_DIR)
#import btyfi


class TestRadius(TestCase):
    _files = ['bad_original.py']

    def setUp(self):
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
        r = Radius.from_vc(vc=self.vc)
        r.btyfi()
        # compare output to desired
        self.assert_(filecmp.cmp(bad, better))

        # Run again
        r.btyfi()
        self.assert_(filecmp.cmp(bad, better))


class MixinTests:

    def test_one_line(self):
        self.check('bad_original.py',
                   'changed_one_line.py',
                   'better_one_line.py')


class TestRadiusGit(TestRadius, MixinTests):
    vc = 'git'


class TestRadiusHg(TestRadius, MixinTests):
    vc = 'hg'
