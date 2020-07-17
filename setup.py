# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='barely-db',
    version='0.8.6',
    description='A database for humans who barely need one.',
    long_description=readme,
    author='Deniz Bozyigit',
    author_email='deniz195@gmail.com',
    url='https://bitbucket.org/battriondev/barely-db.git',
    license=license,
    packages=find_packages(exclude=('tests', 'tests_legacy', 'docs', 'examples')),
    install_requires=['attrs', 'cattrs',],
)
