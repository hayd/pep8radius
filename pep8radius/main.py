from __future__ import print_function

import os
import sys

from pep8radius.radius import Radius
from pep8radius.shell import CalledProcessError  # with 2.6 compat
from pep8radius.vcs import VersionControl

__version__ = version = '0.9.0a'


DEFAULT_IGNORE = 'E24'
DEFAULT_INDENT_SIZE = 4

if sys.platform == 'win32':
    DEFAULT_CONFIG = os.path.expanduser(r'~\.pep8')
else:
    DEFAULT_CONFIG = os.path.join(os.getenv('XDG_CONFIG_HOME') or
                                  os.path.expanduser('~/.config'), 'pep8')
PROJECT_CONFIG = ('setup.cfg', 'tox.ini', '.pep8')


def main(args=None, vc=None, cwd=None, apply_config=False):
    import signal
    import sys

    try:  # pragma: no cover
        # Exit on broken pipe.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:  # pragma: no cover
        # SIGPIPE is not available on Windows.
        pass

    if args is None:
        args = parse_args(sys.argv[1:], apply_config=apply_config)

    try:
        # main
        if args.version:
            print(version)
            sys.exit(0)

        if args.list_fixes:
            from autopep8 import supported_fixes
            for code, description in sorted(supported_fixes()):
                print('{code} - {description}'.format(
                    code=code, description=description))
            sys.exit(0)

        try:
            r = Radius(rev=args.rev, options=args, vc=vc, cwd=cwd)
        except NotImplementedError as e:  # pragma: no cover
            print(e)
            sys.exit(1)
        except CalledProcessError as c:  # pragma: no cover
            # cut off usage and exit
            output = c.output.splitlines()[0]
            print(output)
            sys.exit(c.returncode)

        r.fix()

    except KeyboardInterrupt:  # pragma: no cover
        return 1


def create_parser(root):
    from argparse import ArgumentParser

    # TODO allow passing a config?
    description = ("PEP8 clean only the parts of the files which you have "
                   "touched since the last commit, previous commit or "
                   "branch.")
    epilog = ("Run before you commit, or against a previous commit or "
              "branch before merging.")
    parser = ArgumentParser(description=description,
                            epilog=epilog)

    parser.add_argument('rev',
                        help='commit or name of branch to compare against',
                        nargs='?')

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument('--version',
                       help='print version number and exit',
                       action='store_true')
    group.add_argument('--config-file',
                       default='',
                       help='path to pep8 config file')

    parser.add_argument('-v', '--verbose', action='count', dest='verbose',
                        default=0,
                        help='print verbose messages; '
                        'multiple -v result in more verbose messages')
    parser.add_argument('-d', '--diff', action='store_true', dest='diff',
                        help='print the diff of fixed source vs original')
    parser.add_argument('-i', '--in-place', action='store_true',
                        help="make the changes in place")
    parser.add_argument('-f', '--docformatter', action='store_true',
                        help='fix docstrings for PEP257 using docformatter')
    parser.add_argument('--no-color', action='store_true',
                        help='do not print diffs in color')

    # autopep8 options
    parser.add_argument('-p', '--pep8-passes', metavar='n',
                        default=-1, type=int,
                        help='maximum number of additional pep8 passes '
                        '(default: infinite)')
    parser.add_argument('-a', '--aggressive', action='count', default=0,
                        help='enable non-whitespace changes; '
                        'multiple -a result in more aggressive changes')
    parser.add_argument('--experimental', action='store_true',
                        help='enable experimental fixes')
    parser.add_argument('--exclude', metavar='globs',
                        help='exclude file/directory names that match these '
                        'comma-separated globs')
    parser.add_argument('--list-fixes', action='store_true',
                        help='list codes for fixes; '
                        'used by --ignore and --select')
    parser.add_argument('--ignore', metavar='errors', default='',
                        help='do not fix these errors/warnings '
                        '(default: {0})'.format(DEFAULT_IGNORE))
    parser.add_argument('--select', metavar='errors', default='',
                        help='fix only these errors/warnings (e.g. E4,W)')
    parser.add_argument('--max-line-length', metavar='n', default=79, type=int,
                        help='set maximum allowed line length '
                        '(default: %(default)s)')
    parser.add_argument('--indent-size', default=DEFAULT_INDENT_SIZE,
                        type=int, metavar='n',
                        help='number of spaces per indent level '
                             '(default %(default)s)')
    # docformatter options
    parser.add_argument('--no-blank', dest='post_description_blank',
                        action='store_false',
                        help='do not add blank line after description; '
                             'used by docformatter')
    parser.add_argument('--pre-summary-newline',
                        action='store_true',
                        help='add a newline before the summary of a '
                             'multi-line docstring; used by docformatter')
    parser.add_argument('--force-wrap', action='store_true',
                        help='force descriptions to be wrapped even if it may '
                             'result in a mess; used by docformatter')

    return parser


def apply_config_defaults(parser, arguments, root):
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('--config-file', default='')
    config_file = p.parse_known_args(arguments)[0].config_file
    config_file = os.path.expanduser(config_file)

    try:
        from ConfigParser import SafeConfigParser, NoSectionError
    except:
        from configparser import SafeConfigParser, NoSectionError
    config = SafeConfigParser()
    if config_file:
        config.read(config_file)
    else:
        config.read(config_files(root))
    try:
        defaults = dict(config.items("pep8"))
        parser.set_defaults(**defaults)
        # TODO could also get docformatter ?
    except NoSectionError:
        pass  # just do nothing, potentially this could raise ?
    return parser


def parse_args(arguments=None, root=None, apply_config=False):
    if arguments is None:
        arguments = []
    if root is None:
        root = VersionControl.which().root_dir()

    parser = create_parser(root)
    if apply_config:
        apply_config_defaults(parser, arguments, root=root)
    args = parser.parse_args(arguments)

    # sanity check args (from autopep8)
    if args.max_line_length <= 0:  # pragma: no cover
        parser.error('--max-line-length must be greater than 0')

    if args.select:
        args.select = _split_comma_separated(args.select)

    if args.ignore:
        args.ignore = _split_comma_separated(args.ignore)
    elif not args.select and args.aggressive:
        # Enable everything by default if aggressive.
        args.select = ['E', 'W']
    else:
        args.ignore = _split_comma_separated(DEFAULT_IGNORE)

    if args.exclude:
        args.exclude = _split_comma_separated(args.exclude)
    else:
        args.exclude = []

    return args


def config_files(root):
    """Note that later configs files overwrite earlier ones.

    That is, later ones are more important. It may be better to check whether
    any locals exist, and if they do use them else use DEFAULT_CONFIG.
    Both are easy to implement, just need to pick a route (could even
    be a config option).

    """
    return [DEFAULT_CONFIG] + [os.path.join(root, c) for c in PROJECT_CONFIG]


def _split_comma_separated(string):
    """Return a set of strings."""
    return set(filter(None, string.split(',')))


if __name__ == "__main__":  # pragma: no cover
    main(apply_config=True)
