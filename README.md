pep8radius aka Better-Than-You-Found-It (btyfi) 
-----------------------------------------------

Clean (using autopep8) only the parts of the files which you have touched in the last commit, or against another commit/branch.

Pep8 "storms" (fixing pep8 infractions across the entire project) often cause merge conflicts and break git blame, but you can still "leave it better than you found it" by ensuring that the parts of the project which you touch satisfy pep8.

Currently Supports
------------------
git and hg

Usage
-----

- Move to project directory
- Make some changes to the project
- Run pep8radius
- Commit your changes

Against a branch you can use the same syntax as with git diff:

- pep8radius master  # branch name
- pep8radius c12166f    # commit hash

*Note: can also use btyfi alias for pep8radius.*