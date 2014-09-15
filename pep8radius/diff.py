from difflib import unified_diff
import os
import re

def line_numbers_from_file_udiff(udiff):
    """Parse a udiff, return iterator of tuples of (start, end) line numbers.

    Note: returned in descending order (as autopep8 can +- lines)

    """
    chunks = re.split('\n@@ [^\n]+\n', udiff)[:0:-1]

    line_numbers = re.findall('@@\s[+-]\d+,\d+ \+(\d+)', udiff)
    line_numbers = list(map(int, line_numbers))[::-1]

    # Note: these were reversed as can modify number of lines
    for c, start in zip(chunks, line_numbers):
        ilines = enumerate((line for line in c.splitlines()
                            if not line.startswith('-')),
                           start=start)
        added_lines = [i for i, line in ilines if line.startswith('+')]
        if added_lines:
            yield (added_lines[0], added_lines[-1])


def udiff_lines_fixed(u):
    """Count lines fixed (removed) in udiff.

    """
    removed_changes = re.findall('\n\-', u)
    return len(removed_changes)

def get_diff(original, fixed, file_name,
             original_label='original', fixed_label='fixed'):
    """Return text of unified diff between original and fixed."""
    original, fixed = original.splitlines(True), fixed.splitlines(True)
    newline = '\n'
    diff = unified_diff(original, fixed,
                        os.path.join(file_name, original_label),
                        os.path.join(file_name, fixed_label),
                        lineterm=newline)
    text = ''
    for line in diff:
        text += line
        # Work around missing newline (http://bugs.python.org/issue2142).
        if not line.endswith(newline):
            text += newline + r'\ No newline at end of file' + newline
    return text
