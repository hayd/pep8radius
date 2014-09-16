from tests.test_radius import TestRadius, MixinTests
from tests.util import *


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


# Some additional vcs funtionality not provided in pep8radius
class MixinVcs(object):

    @classmethod
    def save_and_commit(cls, contents, f):
        save(contents, f)
        return cls.successfully_commit_files([f])

    @classmethod
    def init_vc(cls, cwd=TEMP_DIR):
        cls.delete_repo(cwd=cwd)
        success = cls.create_repo(cwd=cwd)
        committed = cls.save_and_commit('a=1;', 'a.py')
        return success and committed


class MixinGit(MixinVcs):

    @staticmethod
    def delete_repo(cwd=TEMP_DIR):
        temp_path = os.path.join(cwd, '.git')
        remove_dir(temp_path)

    @staticmethod
    def create_repo(cwd=TEMP_DIR):
        try:
            shell_out(["git", "init"], cwd=cwd)
            return True
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def successfully_commit_files(file_names,
                                  commit="initial_commit",
                                  cwd=TEMP_DIR):
        try:
            shell_out(["git", "add"] + file_names, cwd=cwd)
            shell_out(["git", "commit", "-m", commit], cwd=cwd)
            with from_dir(cwd):
                return Git().current_branch()
        except (OSError, CalledProcessError):
            return False

    @staticmethod
    def checkout(branch, create=False, cwd=TEMP_DIR):
        if create:
            shell_out(["git", "checkout", '-b', branch], cwd=cwd)
        else:
            shell_out(["git", "checkout", branch], cwd=cwd)


class MixinHg(MixinVcs):

    @staticmethod
    def delete_repo(cwd=TEMP_DIR):
        remove_dir(os.path.join(cwd, '.hg'))

    @staticmethod
    def create_repo(cwd=TEMP_DIR):
        try:
            shell_out(["hg", "init"], cwd=cwd)
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
        if create:
            shell_out(["hg", "branch", branch], cwd=cwd)
        else:
            shell_out(["hg", "update", "--check", branch], cwd=cwd)


class MixinBzr(MixinVcs):

    @staticmethod
    def delete_repo(cwd=TEMP_DIR):
        remove_dir(os.path.join(cwd, '.bzr'))

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


class TestRadiusGit(TestRadius, MixinGit, MixinTests):
    vc = 'git'


class TestRadiusHg(TestRadius, MixinHg, MixinTests):
    vc = 'hg'


class TestRadiusBzr(TestRadius, MixinBzr, MixinTests):
    vc = 'bzr'
