"""This module defines the Radius class, which is where the "meat" of the
pep8radius machinery is done. The important methods are fix, fix_file and
fix_line_range.

The vc attribute is a subclass of VersionControl defined in the vcs
module (provides helper methods for the different vcs e.g. git).

"""

from __future__ import print_function

from sys import version_info

from pep8radius.diff import get_diff, udiff_lines_fixed, print_diff
from pep8radius.vcs import VersionControl


if version_info[0] > 2:  # py3, pragma: no cover
    basestring = str


class Radius(object):

    """PEP8 clean only the parts of the files touched since the last commit, a
    previous commit or branch."""

    def __init__(self, rev=None, options=None, vc=None, cwd=None):
        if vc is None:
            vc = VersionControl.which()
        elif isinstance(vc, basestring):
            vc = VersionControl.from_string(vc)
        else:
            assert(issubclass(vc, VersionControl))
        self.vc = vc(cwd=cwd)

        # pep8radius specific options
        self.rev = self.vc.branch_point(rev)
        from pep8radius.main import parse_args
        self.options = options if options else parse_args([''])
        self.verbose = self.options.verbose
        self.in_place = self.options.in_place
        self.diff = self.options.diff
        self.color = not self.options.no_color

        # autopep8 specific options
        self.options.verbose = max(0, self.options.verbose - 1)
        self.options.in_place = False
        self.options.diff = False

        # Note: This may raise a CalledProcessError, if it does it means
        # that there's been an error with the version control command.
        self.filenames_diff = self.vc.get_filenames_diff(self)

    def fix(self):
        """Runs fix_file on each modified file.

        - Prints progress and diff depending on options.

        """
        n = len(self.filenames_diff)
        _maybe_print('Applying autopep8 to touched lines in %s file(s).' % n)

        total_lines_changed = 0
        pep8_diffs = []
        for i, file_name in enumerate(self.filenames_diff, start=1):
            _maybe_print('%s/%s: %s: ' % (i, n, file_name), end='')
            _maybe_print('', min_=2)

            p_diff = self.fix_file(file_name)
            lines_changed = udiff_lines_fixed(p_diff) if p_diff else 0
            total_lines_changed += lines_changed

            if p_diff and self.diff:
                pep8_diffs.append(p_diff)

        if self.in_place:
            _maybe_print('pep8radius fixed %s lines in %s files.'
                         % (total_lines_changed, n),
                         verbose=self.verbose)
        else:
            _maybe_print('pep8radius would fix %s lines in %s files.'
                         % (total_lines_changed, n),
                         verbose=self.verbose)

        if self.diff:
            for diff in pep8_diffs:
                print_diff(diff, color=self.color)

    def fix_file(self, file_name):
        """Apply autopep8 to the diff lines of a file.

        - Returns the diff between original and fixed file.
        - If self.in_place then this writes the the fixed code the file_name.
        - Prints dots to show progress depending on options.

        """
        # We hope that a CalledProcessError would have already raised
        # during the init if it were going to raise here.
        modified_lines = self.vc.modified_lines(self, file_name)

        return fix_file(file_name, modified_lines, self.options,
                        in_place=self.in_place, diff=True,
                        verbose=self.verbose)


def fix_file(file_name, line_ranges, options=None, in_place=False,
             diff=False, verbose=0):
    """Calls fix_code on the source code from the passed in file over the given
    line_ranges.

    - If diff then this returns the udiff for the changes, otherwise
    returns the fixed code.
    - If in_place the changes are written to the file.

    """
    import codecs
    try:
        with codecs.open(file_name, 'r', encoding='utf-8') as f:
            original = f.read()
    except IOError:
        # file has been removed
        return ''

    fixed = fix_code(original, line_ranges, options, verbose=verbose)

    if in_place:
        with codecs.open(file_name, 'w', encoding='utf-8') as f:
            f.write(fixed)

    return get_diff(original, fixed, file_name) if diff else fixed


def fix_code(source_code, line_ranges, options=None, verbose=0):
    """Apply autopep8 over the line_ranges, returns the corrected code.

    Note: though this is not checked for line_ranges should not overlap.

    Example
    -------
    >>> code = "def f( x ):\n  if True:\n    return 2*x"
    >>> fix_code(code, [(1, 1), (3, 3)])
    "def f(x):\n  if True:\n      return 2 * x\n"

    """
    if options is None:
        parse_args()

    line_ranges = reversed(line_ranges)
    # Apply line fixes "up" the file (i.e. in reverse) so that
    # fixes do not affect changes we're yet to make.
    partial = source_code
    for start, end in line_ranges:
        partial = fix_line_range(partial, start, end, options)
        _maybe_print('.', end='', max_=1, verbose=verbose)
    _maybe_print('', max_=1, verbose=verbose)
    fixed = partial
    return fixed


def fix_line_range(source_code, start, end, options):
    """Apply autopep8 (and docformatter) between the lines start and end of
    source."""
    # TODO confirm behaviour outside range (indexing starts at 1)
    start = max(start, 1)

    options.line_range = [start, end]
    from autopep8 import fix_code
    fixed = fix_code(source_code, options)

    try:
        if options.docformatter:
            from docformatter import format_code
            fixed = format_code(
                fixed,
                summary_wrap_length=options.max_line_length - 1,
                description_wrap_length=(options.max_line_length
                                         - 2 * options.indent_size),
                pre_summary_newline=options.pre_summary_newline,
                post_description_blank=options.post_description_blank,
                force_wrap=options.force_wrap,
                line_range=[start, end])
    except AttributeError:  # e.g. using autopep8.parse_args, pragma: no cover
        pass

    return fixed


def _maybe_print(something_to_print, end=None, min_=1, max_=99, verbose=0):
    """Print if verbose is within min_ and max_."""
    if min_ <= verbose <= max_:
        import sys
        print(something_to_print, end=end)
        sys.stdout.flush()
