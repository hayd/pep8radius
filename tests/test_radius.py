from tests.util import *


class TestRadius(TestCase):

    def __init__(self, *args, **kwargs):
        mk_temp_dirs()
        self.using_vc = self.init_vc()
        super(TestRadius, self).__init__(*args, **kwargs)

    def setUp(self):
        success = self.init_vc()
        if not success:
            raise SkipTest("%s not configured correctly" % self.vc)

    def check(self, original, modified, expected,
              test_name='check', options=None,
              cwd=TEMP_DIR, apply_config=False):
        """Modify original to modified, and check that pep8radius turns this
        into expected."""
        temp_file = os.path.join(cwd, 'temp.py')

        with from_dir(cwd):
            options = parse_args(options, apply_config=apply_config)

        # TODO remove this color hack, and actually test printing color diff
        options.no_color = True

        with open(temp_file, 'w') as f:
            f.write(original)
        committed = self.successfully_commit_files([temp_file],
                                                   commit=test_name)

        with open(temp_file, 'w') as f:
            f.write(modified)

        options.verbose = 1
        r = Radius(vc=self.vc, options=options, cwd=cwd)
        with captured_output() as (out, err):
            r.fix()
        self.assertIn('would fix', out.getvalue())
        self.assertNotIn('@@', out.getvalue())
        options.verbose = 0

        options.diff = True
        r = Radius(vc=self.vc, options=options, cwd=cwd)
        with captured_output() as (out, err):
            r.fix()
        exp_diff = get_diff(modified, expected, temp_file)
        self.assert_equal(out.getvalue(), exp_diff, test_name)
        options.diff = False

        options.in_place = True
        r = Radius(vc=self.vc, options=options, cwd=cwd)
        # Run pep8radius
        r.fix()

        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

        # Run pep8radius again, it *should* be that this doesn't do anything.
        out = pep8radius_main(options, vc=self.vc, cwd=cwd)
        self.assertEqual(out, '')

        with open(temp_file, 'r') as f:
            result = f.read()
        self.assert_equal(result, expected, test_name)

    def assert_equal(self, result, expected, test_name):
        """like assertEqual but with a nice diff output if not equal."""
        self.assertEqual(result, expected,
                         get_diff(expected, result, test_name,
                                  'expected', 'result'))


class MixinTests:

    """All Radius tests are placed in this class."""

    def test_one_line(self):
        original = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_one_line')

    def test_one_line_from_subdirectory(self):
        original = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_one_line',
                   cwd=SUBTEMP_DIR)

    def test_with_docformatter(self):
        original = 'def poor_indenting():\n  """       Great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  """  Very great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  """  Very great function"""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected, 'test_without_docformatter')

        expected = 'def poor_indenting():\n  """Very great function."""\n  a = 1\n  b = 2\n  return a + b\n\n\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        self.check(original, modified, expected,
                   'test_with_docformatter', ['--docformatter'])

    def test_bad_rev(self):
        with captured_output() as (out, err):
            self.assertRaises(CalledProcessError,
                              lambda x: Radius(rev=x,
                                               vc=self.vc,
                                               cwd=TEMP_DIR),
                              'random_junk_sha')

    def test_earlier_revision(self):
        if self.vc == 'bzr':
            raise SkipTest("TODO get me working")

        start = self.save_and_commit('a=1;', 'AAA.py')
        self.checkout('ter', create=True)
        self.save_and_commit('b=1;', 'BBB.py')
        tip = self.save_and_commit('c=1;', 'CCC.py')
        save('c=1', 'CCC.py')

        args = parse_args(['--diff', '--no-color'])
        r = Radius(rev=start, options=args, vc=self.vc, cwd=TEMP_DIR)
        with captured_output() as (out, err):
            r.fix()
        diff = out.getvalue()

        files = [os.path.join(TEMP_DIR, f) for f in ['BBB.py', 'CCC.py']]

        exp_diff = get_diff_many(['b=1;', 'c=1'],
                                 ['b = 1\n', 'c = 1\n'],
                                 files)
        self.assert_equal(diff, exp_diff, 'earlier_revision')

        # TODO test the diff is correct

    def test_deleted_file(self):
        os.remove(os.path.join(TEMP_DIR, 'a.py'))
        args = parse_args(['--diff', '--no-color'])
        r = Radius(options=args, vc=self.vc, cwd=TEMP_DIR)
        with captured_output() as (out, err):
            r.fix()
        self.assertEqual(out.getvalue(), '')

    def test_exclude(self):
        self.save_and_commit('b=1;', 'BBB.py')
        save('b=1', 'BBB.py')
        args = parse_args(['--diff', '--no-color', '--exclude=BBB.py'])
        r = Radius(options=args, vc=self.vc, cwd=TEMP_DIR)
        with captured_output() as (out, err):
            r.fix()
        self.assertEqual(out.getvalue(), '')

    def test_config(self):
        LOCAL_CONFIG = os.path.join(TEMP_DIR, '.pep8')
        with open(LOCAL_CONFIG, mode='w') as f:
            f.write("[pep8]\nindent-size=2")
        original = "def f(x):\n    return 2*x\n"
        modified = "def f(x):\n    return 3*x\n"
        expected = "def f(x):\n  return 3 * x\n"
        self.check(original, modified, expected,
                   'test_config', [],
                   apply_config=True)
        remove(LOCAL_CONFIG)


class TestRadiusFromDiff(TestCase):

    def test_from_diff(self):
        original = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=2; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        modified = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na=1; b=42; c=3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        expected = 'def poor_indenting():\n  a = 1\n  b = 2\n  return a + b\n\nfoo = 1; bar = 2; print(foo * bar)\na = 1\nb = 42\nc = 3\nd=7\n\ndef f(x = 1, y = 2):\n    return x + y\n'
        diff = get_diff(original, modified, 'foo.py')
        with open(os.path.join(TEMP_DIR, 'foo.py'), 'w') as f:
            f.write(modified)
        args = parse_args(['--diff', '--no-color'])
        r = Radius.from_diff(diff, options=args, cwd=TEMP_DIR)
        with captured_output() as (out, err):
            r.fix()
        exp_diff = get_diff(modified, expected, 'foo.py')
        self.assertEqual(out.getvalue(), exp_diff)

if __name__ == '__main__':
    test_main()
