from __future__ import absolute_import

from tests.util import *

# TODO read diffs from files
class TestUDiffParsing(TestCase):
    def test_udiff_parsing(self):
        example_udiff = """@@ -51,6 +51,9 @@ except ImportError:  # pragma: no cover
                 self.cmd, self.returncode)
     subprocess.CalledProcessError = CalledProcessError

+class AbstractMethodError(NotImplementedError):
+    pass
+

 def shell_out(cmd, stderr=STDOUT):
     out = check_output(cmd, stderr=stderr, universal_newlines=True)
@@ -418,15 +421,12 @@ class Radius(object):
             return self.merge_base(rev, current)

     # abstract methods
-    # TODO something with these to appease landscape
-    # with_metaclass http://stackoverflow.com/a/18513858/1240268 ?
-    # six is a rather heavy dependency however
-    # def file_diff_cmd(self, file_name): pass
-    # def filenames_diff_cmd(self): pass
-    # def parse_diff_filenames(self, diff_files): pass
-    # def root_dir(self): pass
-    # def current_branch(self): pass
-    # def merge_base(self): pass
+    def file_diff_cmd(self, file_name): raise AbstractMethodError()
+    def filenames_diff_cmd(self): raise AbstractMethodError()
+    def parse_diff_filenames(self, diff_files): raise AbstractMethodError()
+    def root_dir(self): raise AbstractMethodError()
+    def current_branch(self): raise AbstractMethodError()
+    def merge_base(self): raise AbstractMethodError()


 # #####   udiff parsing   #####
@@ -441,6 +441,7 @@ def line_numbers_from_file_udiff(udiff):
     chunks = re.split('\n@@[^\n]+\n', udiff)[:0:-1]

     line_numbers = re.findall('(?<=@@\s[+-])\d+(?=,\d+)', udiff)
+    import pdb; pdb.set_trace()
     line_numbers = list(map(int, line_numbers))[::-1]

     # Note: these were reversed as can modify number of lines
"""
        lines = list(line_numbers_from_file_udiff(example_udiff))
        assert(lines == [(447, 447), (424, 429)])


if __name__ == '__main__':
    test_main()
