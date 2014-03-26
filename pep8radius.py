import argparse
import re
from subprocess import check_output, STDOUT, CalledProcessError
from sys import exit


def main():
    description = "pep8 only the files you've touched."
    epilog = ("run before you do a commit to tidy, "
              " or against a branch before merging.")
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

    pep8radius(rev=args.rev, verbose=args.verbose)


def pep8radius(rev=None, verbose=False):
    if rev is None:
        cmd = ['git', 'diff', '--name-only']
    else:
        cmd = ['git', 'diff', rev, '--name-only']

    try:
        diff_files = check_output(cmd, stderr=STDOUT)
    except(CalledProcessError) as c:
        # cut off usage of git diff and exit
        output = c.output.splitlines()[0]
        print(output)
        exit(c.returncode)

    for f in diff_files.splitlines():
        change_line_ranges(f, verbose=verbose)


def change_line_ranges(f, rev=None, verbose=False):
    # Presumably this would have raised above it was going to raise...
    if rev is None:
        cmd = ['git', 'diff', f]
    else:
        cmd = ['git', 'diff', rev, f]

    udiffs = [line for line in check_output(cmd).splitlines()
              if line.startswith(b'@@')][::-1]
    # Note: we do this backwards, as autopep8 can add/remove lines

    if verbose:
        print('Applying autopep8 to lines in %s:' % f)
    for u in udiffs:
        start, end = map(str,
                         udiff_start_and_end(u.decode('utf-8')))
        if verbose:
            print('- between %s and %s' % (start, end))
        pep_log = check_output(
            ['autopep8', '--in-place', '--range', start, end, f])
    if verbose:
        print ('Completed pep8-radius on %s\n' % f)


def udiff_start_and_end(u):
    """
    Extract start line and end from udiff

    Example
    -------
    '@@ -638,9 +638,17 @@ class GroupBy(PandasObject):'
    Returns the start line 638 and end line (638 + 17) (the lines added).

    """
    # I *think* we only care about the + lines?
    line_numbers = re.findall('(?<=[+])\d+,\d+', u)[0].split(',')
    line_numbers = list(map(int, line_numbers))
    return line_numbers[0], sum(line_numbers)


if __name__ == "__main__":
    main()
