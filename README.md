pep8radius aka Better-Than-You-Found-It (btyfi) 
-----------------------------------------------

[PEP8](http://legacy.python.org/dev/peps/pep-0008/) clean only the parts of the files which you have touched since the last commit, previous commit or branch.

[![Current PyPi Version](http://img.shields.io/pypi/v/pep8radius.svg)](https://pypi.python.org/pypi/pep8radius)
[![MIT licensed](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://choosealicense.com/licenses/mit/)
[![Travis CI Status](http://img.shields.io/travis/hayd/btyfi.svg)](https://travis-ci.org/hayd/btyfi/builds)
[![PyPi Monthly Downloads](http://img.shields.io/pypi/dm/pep8radius.svg)](https://pypi.python.org/pypi/pep8radius)

Fixing the entire project of PEP8 infractions ("PEP8 storms") can lead to merge conflicts, add noise to merges / pull requests and break (git) blame. pep8radius solves this problem by fixing only those PEP8 infractions incontained on the lines of the project which you've been working, leaving these sections "better than you found it" whilst keeping your commits focused on the areas of the codebase you were actually working on.

Installation
------------
From pip:

```sh
$ pip install pep8radius
```

Requirements
------------
pep8radius requires [autopep8](https://pypi.python.org/pypi/autopep8), which in turn requires [pep8](https://pypi.python.org/pypi/pep8). It also requires a version control system installed on your system...

VCS Support
-----------
[Git](http://git-scm.com/) and [Mecurial (hg)](http://mercurial.selenic.com/). Please request support for other version control systems on [github](https://github.com/hayd/btyfi).

Usage
-----
- Move to project directory
- Make some changes to the project
- `Run pep8radius --dry-run # don't make the changes to files, just view the diff`
- `Run pep8radius           # apply the fixes`
- Commit your changes

Against a branch you can use the same syntax as with git diff:

```sh
$ pep8radius master   # branch name
$ pep8radius c12166f  # commit hash

$ pep8radius master --dry-run  # these work with other options too
```

*Note: can also use `btyfi` alias for `pep8radius`.*

Options
-------

```
usage: btyfi.py [-h] [--version] [-v] [-d] [--dry-run] [-p n] [-a]
                [--experimental] [--exclude globs] [--list-fixes]
                [--ignore errors] [--select errors] [--max-line-length n]
                [--indent-size n]
                [rev]

positional arguments:
  rev                   commit or name of branch to compare against

optional arguments:
  -h, --help            show this help message and exit
  --version             print version number and exit
  -v, --verbose         print verbose messages; multiple -v result in more
                        verbose messages (passed to autopep8)
  -d, --diff            print the diff for the fixed source
  --dry-run             do not make the changes in place and print diff

  -p n, --pep8-passes n
                        maximum number of additional pep8 passes (default:
                        infinite)
  -a, --aggressive      enable non-whitespace changes; multiple -a result in
                        more aggressive changes
  --experimental        enable experimental fixes
  --exclude globs       exclude file/directory names that match these comma-
                        separated globs
  --list-fixes          list codes for fixes; used by --ignore and --select
  --ignore errors       do not fix these errors/warnings (default: E24)
  --select errors       fix only these errors/warnings (e.g. E4,W)
  --max-line-length n   set maximum allowed line length (default: 79)
  --indent-size n       number of spaces per indent level (default 4)
```
*For more information about these options see [autopep8](https://pypi.python.org/pypi/autopep8).*
