pep8radius
----------

[PEP8](http://legacy.python.org/dev/peps/pep-0008/) clean only the parts of
the files touched since the last commit, a previous commit or (the merge-base
of) a branch.

[![Current PyPi Version](http://img.shields.io/pypi/v/pep8radius.svg)](https://pypi.python.org/pypi/pep8radius)
[![MIT licensed](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://choosealicense.com/licenses/mit/)
[![Travis CI Status](http://img.shields.io/travis/hayd/pep8radius.svg)](https://travis-ci.org/hayd/pep8radius/builds)
[![Coverage Status](http://img.shields.io/coveralls/hayd/pep8radius.svg)](https://coveralls.io/r/hayd/pep8radius)
[![PyPi Monthly Downloads](http://img.shields.io/pypi/dm/pep8radius.svg)](https://pypi.python.org/pypi/pep8radius)


Fixing the entire project of PEP8 infractions ("PEP8 storms") can lead to merge
conflicts, add noise to merges / pull requests and break (git) blame. pep8radius
solves this problem by fixing only those PEP8 infractions incontained on the
lines of the project which you've been working, leaving these sections "better
than you found it" whilst keeping your commits focused on the areas of the
codebase you were actually working on.

Requirements
------------
pep8radius uses [autopep8](https://pypi.python.org/pypi/autopep8), and in turn
[pep8](https://pypi.python.org/pypi/pep8). The docformatter option, to fix
docstrings, uses [docformatter](https://pypi.python.org/pypi/docformatter).

You can also use [yapf](https://pypi.python.org/pypi/yapf) as an alternative
back-end.

Installation
------------
From pip:

```sh
$ pip install pep8radius
```

Usage
-----
![Usage gif of pep8radius](https://cloud.githubusercontent.com/assets/1931852/4259885/18a7e75e-3b1a-11e4-9413-d92f9b170b70.gif)

- Move to project directory
- Make some changes to the project
- Run `pep8radius --diff       # view a diff of proposed fixed`
- Run `pep8radius --in-place   # apply the fixes`
- Commit your changes

Against a branch you can use the same syntax as with git diff:

```sh
$ pep8radius master   # branch name to compare against (compares against merge-base)
$ pep8radius c12166f  # commit hash

$ pep8radius master --in-place  # these work with other options too
```

You can also fix docstrings ([PEP257](http://legacy.python.org/dev/peps/pep-0257/)) using
the [docformatter](https://pypi.python.org/pypi/docformatter) option:

```sh
$ pep8radius --docformatter --diff
```

*Note: can also use `btyfi` alias for `pep8radius`.*

---

It can be nice to pipe the diff to [cdiff](https://pypi.python.org/pypi/cdiff) (which
makes diffs pretty and has lots of options):

```sh
$ pep8radius --diff --no-color | cdiff
$ pep8radius --diff --no-color | cdiff --side-by-side
```

You can get strange results if you don't use no-color.  
I actually use the following git
alias (which allows `git rad` and `git rad -i`):
```sh
[alias]
    rad = !pep8radius master --diff --no-color $@ | cdiff --side-by-side
```
which outputs the corrections as follows:

![git rad](https://cloud.githubusercontent.com/assets/1931852/4259933/f0589480-3b1c-11e4-89cf-565c28da700a.png)

---

You can pipe in a diff directly, to fix the lines modified in it with
`--from-diff` (this is somewhat experimental, please report failing diffs!).  
For example:

```sh
$ git diff master | pep8radius --diff --from-diff=-
```

yapf
----
To use [yapf](https://pypi.python.org/pypi/yapf) as an alternative back-end, you
can pass the `--yapf` option:
```
$ pep8radius master --diff --yapf

$ pep8radius master --diff --yapf --style=google
```
*Note: This ignores autopep8 and docformatter specific arguments.*

Config Files
------------
pep8radius looks for configuration files as described in the
[pep8 docs](http://pep8.readthedocs.org/en/latest/intro.html#configuration).

At the project level, you may have a `setup.cfg` which includes a pep8 section,
you can use this to define defaults for pep8radius and autopep8:

```
[pep8]
rev = master
ignore = E226,E302,E41
max-line-length = 160
```

By default, this will look for a user level default, you can suppress this
by passing a blank to `global_config`:

```
[pep8]
rev = staging
global_config =
```

or perhaps you want to use yapf with google style:

```
[pep8]
rev = master
yapf = True
style = google
```
*Note: style can also be a config file, or a dict (see the yapf docs).*

VCS Support
-----------
[Git](http://git-scm.com/), [Mecurial (hg)](http://mercurial.selenic.com/), (tentatively)
[Bazaar](http://bazaar.canonical.com/en/). Please request support for other version
control systems on [github](https://github.com/hayd/pep8radius/issues/5).

Options
-------

```sh
$ pep8radius --help

usage: pep8radius [-h] [--version] [-d] [-i] [--no-color] [-v]
                  [--from-diff DIFF] [-p n] [-a] [--experimental]
                  [--exclude globs] [--list-fixes] [--ignore errors]
                  [--select errors] [--max-line-length n] [--indent-size n]
                  [-f] [--no-blank] [--pre-summary-newline] [--force-wrap]
                  [--global-config GLOBAL_CONFIG] [--ignore-local-config]
                  [rev]

PEP8 clean only the parts of the files which you have touched since the last
commit, a previous commit or (the merge-base of) a branch.

positional arguments:
  rev                   commit or name of branch to compare against

optional arguments:
  -h, --help            show this help message and exit
  --version             print version number and exit
  -d, --diff            print the diff of fixed source vs original
  -i, --in-place        make the fixes in place; modify the files
  --no-color            do not print diffs in color (default is to use color)
  -v, --verbose         print verbose messages; multiple -v result in more
                        verbose messages (one less -v is passed to autopep8)
  --from-diff DIFF      Experimental: rather than calling out to version
                        control, just pass in a diff; the modified lines will
                        be fixed

pep8:
  Pep8 options to pass to autopep8.

  -p n, --pep8-passes n
                        maximum number of additional pep8 passes (default:
                        infinite)
  -a, --aggressive      enable non-whitespace changes; multiple -a result in
                        more aggressive changes
  --experimental        enable experimental fixes
  --exclude globs       exclude file/directory names that match these comma-
                        separated globs
  --list-fixes          list codes for fixes and exit; used by --ignore and
                        --select
  --ignore errors       do not fix these errors/warnings (default: E24)
  --select errors       fix only these errors/warnings (e.g. E4,W)
  --max-line-length n   set maximum allowed line length (default: 79)
  --indent-size n       number of spaces per indent level (default 4)

docformatter:
  Fix docstrings for PEP257.

  -f, --docformatter    Use docformatter
  --no-blank            Do not add blank line after description
  --pre-summary-newline
                        add a newline before the summary of a multi-line
                        docstring
  --force-wrap          force descriptions to be wrapped even if it may result
                        in a mess

config:
  Change default options based on global or local (project) config files.

  --global-config filename
                        path to global pep8 config file; if this file does not
                        exist then this is ignored (default: ~/.config/pep8)
  --ignore-local-config
                        don't look for and apply local config files; if not
                        passed, defaults are updated with any config files in
                        the project's root dir

yapf:
  Options for yapf, alternative to autopep8. Currently any other options are
  ignored.

  -y, --yapf            Use yapf rather than autopep8. This ignores other
                        arguments outside of this group.
  --style               style either pep8, google, name of file with
                        stylesettings, or a dict

Run before you commit, against a previous commit or branch before merging.
```

*For more information about these options see [autopep8](https://pypi.python.org/pypi/autopep8).*

As a module
-----------

Pep8radius also exports lightweight wrappers around autopep8 so that you can
fix line ranges of your code with `fix_code` or `fix_file`.

Here's the example "bad code" from [autopep8's README](https://github.com/hhatto/autopep8/blob/master/README.rst#usage):

```py
import math, sys;

def example1():
    ####This is a long comment. This should be wrapped to fit within 72 characters.
    some_tuple=(   1,2, 3,'a'  );
    some_variable={'long':'Long code lines should be wrapped within 79 characters.',
    'other':[math.pi, 100,200,300,9876543210,'This is a long string that goes on'],
    'more':{'inner':'This whole logical line should be wrapped.',some_tuple:[1,
    20,300,40000,500000000,60000000000000000]}}
    return (some_tuple, some_variable)
def example2(): return {'has_key() is deprecated':True}.has_key({'f':2}.has_key(''));
class Example3(   object ):
    def __init__    ( self, bar ):
     #Comments should have a space after the hash.
     if bar : bar+=1;  bar=bar* bar   ; return bar
     else:
                    some_string = """
               Indentation in multiline strings should not be touched.
Only actual code should be reindented.
"""
                    return (sys.path, some_string)
```
You can pep8 fix just the line ranges 1-1 (the imports) and 12-21 (the
`Example3`class) with `pep8radius.fix_code(code, [(1, 1), (12, 21)])` (where
code is a string of the above), which returns the code fixed within those
ranges:
```py
import math
import sys

def example1():
    ####This is a long comment. This should be wrapped to fit within 72 characters.
    some_tuple=(   1,2, 3,'a'  );
    some_variable={'long':'Long code lines should be wrapped within 79 characters.',
    'other':[math.pi, 100,200,300,9876543210,'This is a long string that goes on'],
    'more':{'inner':'This whole logical line should be wrapped.',some_tuple:[1,
    20,300,40000,500000000,60000000000000000]}}
    return (some_tuple, some_variable)
def example2(): return {'has_key() is deprecated':True}.has_key({'f':2}.has_key(''));


class Example3(object):

    def __init__(self, bar):
        # Comments should have a space after the hash.
        if bar:
            bar += 1
            bar = bar * bar
            return bar
        else:
            some_string = """
                       Indentation in multiline strings should not be touched.
Only actual code should be reindented.
"""
            return (sys.path, some_string)
```
You can use `fix_file` to do this directly on a file, which gives you the option
of doing this in place.

```py
pep8radius.fix_code('code.py', [(1, 1), (12, 21)], in_place=True)
```
You can also pass the same arguments to pep8radius script itself using the
`parse_args`. For example ignoring long lines (E501) and use the options from
your global config files:
```py
args = pep8radius.parse_args(['--ignore=E501', '--ignore-local-config'],
                             apply_config=True)
pep8radius.fix_code(code, [(1, 1), (12, 21)], options=args)
```
