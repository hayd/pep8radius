#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import parse
import os
from setuptools import setup
from sys import version_info


NAME = 'pep8radius' #  'Better-Than-You-Found-It'


def version():
    """Return version string."""
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           'pep8radius.py')) as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return parse(line).body[0].value.s

def readme():
    try:
        import pypandoc
        return pypandoc.convert('README.md', 'rst', format='md')
    except (IOError, ImportError):
        with open('README.md') as f:
            return f.read()

INSTALL_REQUIRES = (
    ['autopep8 >= 1.0.2'] +
    (['argparse'] if version_info < (2, 7) else []) +
    ['colorama'] +
    ['docformatter >= 0.6.1']
)

setup(
    name=NAME,
    version=version(),
    description="PEP8 clean only the parts of the files which you have touched"
                " since the last commit, previous commit or branch.",
    long_description=readme(),
    license='MIT License',
    author='Andy Hayden',
    author_email='andyhayden1@gmail.com',
    url='https://github.com/hayd/pep8radius',
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
    test_suite='tests.test_pep8radius',
    py_modules=['pep8radius'],
    zip_safe=False,
    entry_points={'console_scripts': ['btyfi = pep8radius:main',
                                      'pep8radius = pep8radius:main']},
)
