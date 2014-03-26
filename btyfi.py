import argparse
import re
from subprocess import check_output, STDOUT, CalledProcessError
from sys import exit


def main():
    description = ("Tidy up (autopep8) only the lines in the files touched "
                   "in the git branch/commit.")
    epilog = ("Run before you do a commit to tidy, "
              "or against a branch before merging.")
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)
    parser.add_argument('rev',
                        help='commit or name of branch to compare against',
                        nargs='?')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-v', '--verbose',
                       help='print which files/lines are being pep8d',
                       action='store_true')

    args = parser.parse_args()

    try:
        vc = which_version_control()
    except NotImplementedError:
        print("Unknown version control system")
        exit(1)

    btyfi(rev=args.rev, verbose=args.verbose)


def btyfi(rev=None, verbose=False):
    vc = which_version_control()

    if rev is None:
        rev = get_current_branch(vc)

    cmd = filenames_diff_cmd(rev, vc=vc)

    try:
        diff_files = check_output(cmd, stderr=STDOUT)
    except(CalledProcessError) as c:
        # cut off usage of git diff and exit
        output = c.output.splitlines()[0]
        print(output)
        exit(c.returncode)

    diff_files = diff_files.decode('utf-8')
    diff_files = parse_diff_filenames(diff_files, vc=vc)

    for f in diff_files:
        pep8radius_file(f, rev=rev, verbose=verbose, vc=vc)


def pep8radius_file(f, rev, verbose=False, vc='git'):
    # Presumably this would have raised above it was going to raise...
    cmd = file_diff_cmd(f, rev=rev, vc=vc)
    diff = check_output(cmd).decode('utf-8')

    if verbose:
        print('Applying autopep8 to lines in %s:' % f)

    for start, end in line_numbers_from_file_diff(diff):
        autopep8_line_range(f, start, end, verbose=verbose)

    if verbose:
        print ('Completed pep8radius on %s\n' % f)


def autopep8_line_range(f, start, end, verbose=False):
    if verbose:
        print('- between %s and %s' % (start, end))
    pep_log = check_output(['autopep8', '--in-place', '--range',
                            start, end, f])


def which_version_control():
    """
    Try to see if they are using git, hg.
    return git, hg or raise NotImplementedError.

    """
    try:
        git_log = check_output(["git", "log"], stderr=STDOUT)
        return "git"
    except CalledProcessError:
        pass

    try:
        hg_log = check_output(["hg", "log"], stderr=STDOUT)
        return "hg"
    except CalledProcessError:
        pass

    # Not supported (yet)
    raise NotImplementedError("Unknown version control system")


def get_current_branch(vc='git'):
    """
    If no rev is passed we use the current branch.

    """
    if vc == 'git':
        output = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return output.strip().decode('utf-8')

    if vc == 'hg':
        output = check_output(["hg", "id", "-b"])
        ret.strip().decode('utf-8')

    raise NotImplementedError("Unknown version control system")


def filenames_diff_cmd(rev, vc='git'):
    # TODO includes only py files
    if vc == 'git':
        return ['git', 'diff', rev, '--name-only']
    if vc == 'hg':
        return ["hg", "diff", "--stat", "-c", rev]

    raise NotImplementedError("Unknown version control system")


def file_diff_cmd(f, rev, vc='git'):
    if vc == 'git':
        return ['git', 'diff', rev, f]
    if vc == 'hg':
        return ['hg', 'diff', '-c', rev, f]

    raise NotImplementedError("Unknown version control system")


def parse_diff_filenames(diff_files, vc='git'):
    """
    Parse output of filenames_diff_cmd to get list of py files

    """
    if vc == 'git':
        return diff_files.splitlines()
    if vc == 'hg':
        return re.findall('(?<=[$| |\n]).*\.py', diff_lines)

    raise NotImplementedError("Unknown version control system")


def line_numbers_from_file_diff(diff):
    """
    Parse a diff, return iterator of tuples of (start, end) line numbers.

    Note: they are returned in descending order (so as autopep8 can be applied)

    """
    lines_with_line_numbers = [line for line in diff.splitlines()
                               if line.startswith('@@')][::-1]
    # Note: we do this backwards, as autopep8 can add/remove lines

    for u in lines_with_line_numbers:
        start, end = map(str, udiff_line_start_and_end(u))
        yield (start, end)


def udiff_line_start_and_end(u):
    """
    Extract start line and end from udiff line

    Example
    -------
    '@@ -638,9 +638,17 @@ class GroupBy(PandasObject):'
    Returns the start line 638 and end line (638 + 17) (the lines added).

    """
    # I *think* we only care about the + lines?
    line_numbers = re.findall('(?<=[+])\d+,\d+', u)[0].split(',')
    line_numbers = list(map(int, line_numbers))
    # TODO work out if this should this be +3 and -3 ?
    return line_numbers[0], sum(line_numbers)


if __name__ == "__main__":
    main()
