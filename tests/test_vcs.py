from tests.test_radius import TestRadius, MixinTests
from tests.util import *
from tests.util_vcs import *


class TestRadiusNoVCS(TestCase):

    def __init__(self, *args, **kwargs):
        mk_temp_dirs()
        super(TestRadiusNoVCS, self).__init__(*args, **kwargs)

    def test_no_vc(self):

        # self.assertRaises(NotImplementedError, VersionControl.which)
        # This see the above repo, which is pep8radius and using git !
        raise SkipTest("TODO not sure how to test, as we're always in a repo!")

    def test_bad_vc(self):
        self.assertRaises(NotImplementedError,
                          lambda x: Radius(vc=x),
                          'made_up_vc')

    def test_using_vc(self, cwd=TEMP_DIR):
        # TODO dry this and move to TestRadius
        MixinGit.delete_repo()
        MixinHg.delete_repo()
        MixinBzr.delete_repo()

        self.assertFalse(using_hg(cwd=cwd))
        if MixinHg.init_vc(cwd=cwd):
            self.assertTrue(using_hg(cwd=cwd))
            self.assertTrue(isinstance(Radius(vc='hg', cwd=cwd).vc, Hg))

        self.assertFalse(using_bzr(cwd=cwd))
        if MixinBzr.init_vc(cwd=cwd):
            self.assertTrue(using_bzr(cwd=cwd))
            self.assertTrue(isinstance(Radius(vc='bzr', cwd=cwd).vc, Bzr))

        # git is seen before this, as the dir above is git!
        self.assertTrue(using_git(cwd=cwd))
        self.assertTrue(isinstance(Radius(vc='git').vc, Git))


class TestRadiusGit(TestRadius, MixinGit, MixinTests):
    vc = 'git'


class TestRadiusHg(TestRadius, MixinHg, MixinTests):
    vc = 'hg'


class TestRadiusBzr(TestRadius, MixinBzr, MixinTests):
    vc = 'bzr'
