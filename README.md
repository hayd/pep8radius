### pep8-radius

Clean (using autopep8) only the parts of the files which you have touched in the last commit, or against another commit/branch.

Usage:

- Move to project directory
- Run pep8radius

Against a branch you can use the same syntax as with git diff:

- pep8radius master  # branch name
- pep8radius c12166f  # commit hash
