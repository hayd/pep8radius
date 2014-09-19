import autopep8
from tests.util import *


class TestMain(TestCase):

    def test_autopep8_args(self):
        import autopep8

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

    def test_config(self):
        cfg = os.path.join(TEMP_DIR, '.pep8')
        remove(cfg)

        args_before = parse_args(apply_config=False)
        self.assertNotIn('E999', args_before.ignore)

        with open(cfg, mode='w') as f:
            f.write("[pep8]\nignore=E999")
        args_after = parse_args(['--config=%s' % cfg], apply_config=True)
        self.assertIn('E999', args_after.ignore)
        args_after = parse_args(['--config=False'], apply_config=True)
        self.assertNotIn('E999', args_after.ignore)

        remove(cfg)

    def test_help(self):
        self.check_help()

    def test_help_outside_project(self):
        home = os.path.expanduser('~')
        try:
            VersionControl.which(cwd=home)
            raise SkipTest("Home directory is under version control ??")
        except NotImplementedError:
            pass
        self.check_help(cwd=home)

    def check_help(self, cwd=TEMP_DIR):
        help_message = pep8radius_main(['--help'], cwd=cwd)
        self.assertIn("--no-color", help_message)
        self.assertIn("PEP8 clean only the parts of the files", help_message)

if __name__ == '__main__':
    test_main()
