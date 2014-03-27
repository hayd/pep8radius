#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from sys import version_info


VERSION = '0.4'
NAME = 'Better-Than-You-Found-It'  # 'pep8radius'

INSTALL_REQUIRES = (
    ['autopep8'] +
    (['argparse'] if version_info < (2, 7) else [])
)

with open('README.md') as readme:
    setup(
        name=NAME,
        version=VERSION,
        description="Tidy up (autopep8) only the lines in the files touched "
                    "in the git or hg branch/commit.",
        long_description=readme.read(),
        license='MIT License',
        author='Andy Hayden',
        author_email='andyhayden1@gmail.com',
        url='https://github.com/hayd/btyfi',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Software Development :: Quality Assurance',
        ],
        keywords='automation, pep8, format, autopep8, git, hg, mercurial',
        install_requires=INSTALL_REQUIRES,
        test_suite='test.test_btyfi',
        py_modules=['btyfi'],
        zip_safe=False,
        entry_points={'console_scripts': ['btyfi = btyfi:main',
                                          'pep8radius = btyfi:main']},
    )
