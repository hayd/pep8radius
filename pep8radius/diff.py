"""This module contains the helpers for diff creation, printing and extracting
line numbers."""

from __future__ import print_function

import os
import re


def modified_lines_from_udiff(udiff):
    """Extract from a udiff an iterator of tuples of (start, end) line
    numbers."""
    chunks = re.split('\n@@ [^\n]+\n', udiff)[1:]

    line_numbers = re.findall('@@\s[+-]\d+,\d+ \+(\d+)', udiff)
    line_numbers = list(map(int, line_numbers))

    for c, start in zip(chunks, line_numbers):
        ilines = enumerate((line for line in c.splitlines()
                            if not line.startswith('-')),
                           start=start)
        added_lines = [i for i, line in ilines if line.startswith('+')]
        if added_lines:
            yield (added_lines[0], added_lines[-1])


def udiff_lines_fixed(u):
    """Count lines fixed (removed) in udiff."""
    # TODO maybe this should return + and - (and tweak printing in Radius)
    removed_changes = re.findall('\n\-', u)
    return len(removed_changes)


def get_diff(original, fixed, file_name,
             original_label='original', fixed_label='fixed'):
    """Return text of unified diff between original and fixed."""
    original, fixed = original.splitlines(True), fixed.splitlines(True)
    newline = '\n'

    from difflib import unified_diff
    diff = unified_diff(original, fixed,
                        os.path.join(original_label, file_name),
                        os.path.join(fixed_label, file_name),
                        lineterm=newline)
    text = ''
    for line in diff:
        text += line
        # Work around missing newline (http://bugs.python.org/issue2142).
        if not line.endswith(newline):
            text += newline + r'\ No newline at end of file' + newline
    return text


def print_diff(diff, color=True):
    """Pretty printing for a diff, if color then we use a simple color scheme
    (red for removed lines, green for added lines)."""
    import colorama

    if not diff:
        return

    if not color:
        colorama.init = lambda autoreset: None
        colorama.Fore.RED = ''
        colorama.Back.RED = ''
        colorama.Fore.GREEN = ''
        colorama.deinit = lambda: None

    colorama.init(autoreset=True)  # TODO use context_manager
    for line in diff.splitlines():
        if line.startswith('+') and not line.startswith('+++ '):
            # Note there shouldn't be trailing whitespace
            # but may be nice to generalise this
            print(colorama.Fore.GREEN + line)
        elif line.startswith('-') and not line.startswith('--- '):
            split_whitespace = re.split('(\s+)$', line)
            if len(split_whitespace) > 1:  # claim it must be 3
                line, trailing, _ = split_whitespace
            else:
                line, trailing = split_whitespace[0], ''
            print(colorama.Fore.RED + line, end='')
            # give trailing whitespace a RED background
            print(colorama.Back.RED + trailing)
        elif line == '\ No newline at end of file':
            # The assumption here is that there is now a new line...
            print(colorama.Fore.RED + line)
        else:
            print(line)
    colorama.deinit()
