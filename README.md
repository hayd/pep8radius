pep8radius aka Better-Than-You-Found-It (btyfi) 
-----------------------------------------------

Clean (using autopep8) only the parts of the files which you have touched in the last commit, or against another commit/branch.

Pep8 "storms" (fixing pep8 infractions across the entire project) often cause merge conflicts and break git blame, but you can still "leave it better than you found it" by ensuring that the parts of the project which you touch satisfy pep8.

Installation
------------
From pip:

    $ pip install pep8radius

Requirements
------------
requires autopep8, which in turn requires pep8.

Currently Supports
------------------
git and hg (you need your version control to be installed on your system).

Usage
-----
- Move to project directory
- Make some changes to the project
- `Run pep8radius --dry-run # don't make the changes to files, just view the diff`
- `Run pep8radius           # apply the fixes`
- Commit your changes

Against a branch you can use the same syntax as with git diff:

    pep8radius master   # branch name
    pep8radius c12166f  # commit hash

*Note: can also use btyfi alias for pep8radius.*

Options
-------

    usage: btyfi.py [-h] [--version] [-v] [-d] [--dry-run] [-p n] [-a]
                    [--experimental] [--exclude globs] [--list-fixes]
                    [--ignore errors] [--select errors] [--max-line-length n]
                    [--indent-size n]
                    [rev]

    Tidy up (autopep8) only the lines in the files touched in the git
    branch/commit.

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

For more details about these options see autopep8.