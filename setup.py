#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from sys import version_info


VERSION = '0.3'

INSTALL_REQUIRES = (
    ['autopep8'] +
    (['argparse'] if version_info < (2, 7) else [])
)

with open('README.md') as readme:
    setup(
        name='pep8radius',
        version=VERSION,
        description="pep8 only the files you've touched in the git branch/commit.",
        long_description=readme.read(),
        license='MIT License',
        author='Andy Hayden',
        author_email='andyhayden1@gmail.com',
        url='https://github.com/hayd/pep8-radius',
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
        keywords='automation, pep8, format, autopep8, git',
        install_requires=INSTALL_REQUIRES,
        test_suite='test.test_radius',
        py_modules=['pep8radius'],
        zip_safe=False,
        entry_points={'console_scripts': ['pep8radius = pep8radius:main']},
    )
