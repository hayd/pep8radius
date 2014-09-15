from __future__ import absolute_import, print_function

import autopep8
import codecs
import colorama
import docformatter
import glob
import os
import re
import sys

from pep8radius.diff import line_numbers_from_file_udiff, get_diff, udiff_lines_fixed
from pep8radius.shell import (shell_out, shell_out_ignore_exitcode,
                              CalledProcessError)# with 2.6 compat
from pep8radius.vcs import VersionControl


class AbstractMethodError(NotImplementedError):
    pass


class Radius(object):

    def __init__(self, rev=None, options=None, vc=None):
        if vc is None:
            vc = VersionControl.which()
        elif isinstance(vc, basestring):
            vc = VersionControl.from_string(vc)
        else:
            assert(issubclass(vc, VersionControl))
        self.vc = vc()

        # pep8radius specific options
        self.rev = self.vc._branch_point(rev)
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
        self.filenames_diff = self.get_filenames_diff()

    @staticmethod
    def new(rev=None, options=None, vc=None):
        """Create subclass instance of Radius with correct version control

        e.g. RadiusGit if using git

        """
        # TODO delete
        return Radius(rev=rev, options=options, vc=vc)

    def pep8radius(self):
        """PEP8 clean only the parts of the files which you have touched
        since the last commit, previous commit or branch.

        """
        n = len(self.filenames_diff)

        self.p('Applying autopep8 to touched lines in %s file(s).' % n)

        total_lines_changed = 0
        pep8_diffs = []
        for i, file_name in enumerate(self.filenames_diff, start=1):
            self.p('%s/%s: %s: ' % (i, n, file_name), end='')
            self.p('', min_=2)

            p_diff = self.pep8radius_file(file_name)
            lines_changed = udiff_lines_fixed(p_diff) if p_diff else 0
            total_lines_changed += lines_changed
            self.p('fixed %s lines.' % lines_changed, max_=1)

            if p_diff and self.diff:
                pep8_diffs.append(p_diff)

        if self.in_place:
            self.p('pep8radius fixed %s lines in %s files.'
                   % (total_lines_changed, n))
        else:
            self.p('pep8radius would fix %s lines in %s files.'
                   % (total_lines_changed, n))

        if self.diff:
            for diff in pep8_diffs:
                self.print_diff(diff, color=self.color)

    def pep8radius_file(self, file_name):
        """Apply autopep8 to the diff lines of a file.
        Returns the diff between original and fixed file.

        """
        # We hope that a CalledProcessError would have already raised
        # during the init if it were going to raise here.
        cmd = self.vc.file_diff_cmd(self, file_name)
        diff = shell_out_ignore_exitcode(cmd, cwd=self.vc.root)

        try:
            with codecs.open(file_name, 'r', encoding='utf-8') as f:
                original = f.read()
        except IOError:
            # file has been removed
            return False

        # Apply line fixes "up" the file (i.e. in reverse) so that
        # fixes do not affect changes we're yet to make.
        partial = original
        for start, end in self.line_numbers_from_file_diff(diff):
            partial = self.autopep8_line_range(partial, start, end)
            self.p('.', end='', max_=1)
        self.p('', max_=1)
        fixed = partial

        if self.in_place:
            with codecs.open(file_name, 'w', encoding='utf-8') as f:
                f.write(fixed)
        return get_diff(original, fixed, file_name)

    def autopep8_line_range(self, f, start, end):
        """Apply autopep8 between start and end of file f xcasxz."""
        # not sure on behaviour if outside range (indexing starts at 1)
        start = max(start, 1)

        self.options.line_range = [start, end]
        fixed = autopep8.fix_code(f,   self.options)

        if self.options.docformatter:
            fixed = docformatter.format_code(
                fixed,
                summary_wrap_length=self.options.max_line_length - 1,
                description_wrap_length=(self.options.max_line_length
                                         - 2 * self.options.indent_size),
                pre_summary_newline=self.options.pre_summary_newline,
                post_description_blank=self.options.post_description_blank,
                force_wrap=self.options.force_wrap,
                line_range=[start, end])

        return fixed

    def get_filenames_diff(self):
        "Get the py files which have been changed since rev"
        cmd = self.vc.filenames_diff_cmd(self)

        diff_files = shell_out_ignore_exitcode(cmd, cwd=self.vc.root)
        diff_files = self.vc.parse_diff_filenames(diff_files)

        py_files = set(f for f in diff_files if f.endswith('.py'))

        if self.options.exclude:
            # TODO do we have to take this from root dir?
            for pattern in self.options.exclude:
                py_files.difference_update(glob.fnmatch.filter(py_files,
                                                               pattern))

        # This may raise a CalledProcessError,
        # however it should already have been caught upon new.
        root_dir = os.path.abspath(self.vc.root_dir())
        py_files_full = [os.path.join(root_dir,
                                      file_name)
                         for file_name in py_files]

        return sorted(py_files_full)

    def line_numbers_from_file_diff(self, diff):
        "Potentially this is vc specific (if not using udiff)"
        for start, end in line_numbers_from_file_udiff(diff):
            yield start, end

    def p(self, something_to_print, end=None, min_=1, max_=99):
        if min_ <= self.verbose <= max_:
            print(something_to_print, end=end)
            sys.stdout.flush()

    def print_diff(self, diff, color=True):
        if not self.diff or not diff:
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


