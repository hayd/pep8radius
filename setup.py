#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import parse
from setuptools import setup
from sys import version_info


NAME = 'Better-Than-You-Found-It'  # 'pep8radius'


def version():
    """Return version string."""
    with open('btyfi.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return parse(line).body[0].value.s

def readme():
    try:
       import pypandoc
       return pypandoc.convert('README.md', 'rst')
    except (IOError, ImportError):
       return open('README.md').read()

INSTALL_REQUIRES = (
    ['autopep8'] +
    (['argparse'] if version_info < (2, 7) else [])
)

setup(
    name=NAME,
    version=version(),
    description="Tidy up (autopep8) only the lines in the files touched "
                "in the git or hg branch/commit.",
    long_description=readme(),
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
