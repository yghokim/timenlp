#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

requirements = []

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', 'pyyaml']

setup(
    author="Young-Ho Kim",
    author_email='yghokim@younghokim.net',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
    ],
    description="Natural language time expression parser in python, built upon ctparse but focusing on the past time and ranges.",
    install_requires=[
        'python-dateutil>=2.7.3,<3.0.0',
        'regex>=2018.6.6',
        'tqdm>=4.23.4,<5.0.0'
    ],
    license="MIT license",
    include_package_data=True,
    keywords='timenlp time parsing natural language',
    name='timenlp',
    packages=find_packages(include=['timenlp*']),
    package_dir={'timenlp': 'timenlp'},
    package_data={'timenlp': ['models/model.pbz', 'py.typed']},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/yghokim/timenlp',
    version='0.3.8',
    zip_safe=False,
)
