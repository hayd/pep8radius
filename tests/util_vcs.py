"""Some additional vcs funtionality not provided in pep8radius."""

from tests.util import *


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
