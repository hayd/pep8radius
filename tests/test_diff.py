from tests.util import *


class TestUDiffParsing(TestCase):

    def test_udiff_parsing(self):
        with open(os.path.join(TEST_DIR, 'diff1.txt')) as f:
            example_udiff = f.read()
        lines = list(modified_lines_from_udiff(example_udiff))
        assert(lines == [(444, 444), (424, 429), (54, 56)])


if __name__ == '__main__':
    test_main()
