from __future__ import absolute_import

import autopep8
from tests.util import *

class TestRadiusNoVCS(TestCase):

    def __init__(self, *args, **kwargs):
        self.original_dir = os.getcwd()
        super(TestRadiusNoVCS, self).__init__(*args, **kwargs)

    def setUp(self):
        os.chdir(TEMP_DIR)

    def tearDown(self):
        os.chdir(self.original_dir)

    def test_no_vc(self):
        MixinGit.delete_repo()
        MixinHg.delete_repo()

        # self.assertRaises(NotImplementedError, VersionControl.which)
        # This see the above repo, which is pep8radius and using git !
        pass

    def test_bad_vc(self):
        self.assertRaises(NotImplementedError,
                          lambda x: Radius.new(vc=x),
                          'made_up_vc')

    def test_unknown_vc(self):
        # we have pep8radius is uing git...
        self.assertTrue(isinstance(Radius.new(vc='git').vc, Git))

    def test_using_vc(self):
        MixinGit.delete_repo()
        MixinHg.delete_repo()
        MixinBzr.delete_repo()

        self.assertFalse(using_hg())
        if MixinHg.create_repo():
            self.assertTrue(using_hg())

        self.assertFalse(using_bzr())
        if MixinBzr.create_repo():
            self.assertTrue(using_bzr())

        # git is seen before this, as the dir above is git!
        self.assertTrue(using_git())

    def test_autopep8_args(self):
        # TODO see that these are passes on (use a static method in Radius?)

        args = ['hello.py']
        us = parse_args(args)
        them = autopep8.parse_args(args)

        # API change in autopep8, these are now sets rather than lists
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


if __name__ == '__main__':
    test_main()
