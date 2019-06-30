#!/usr/bin/env python

import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

about = {}
with open('iso19794/__init__.py', 'r') as f:
    try:
        exec(f.read(), about)
    except KeyError:
        pass

setuptools.setup(
    name = 'iso19794',
    version = about['__version__'],
    author = about['__author__'],
    author_email = "olivier.heurtier@idemia.com",
    license = about['__license__'],
    description = 'ISO-19794 Image format for Python',
    long_description = long_description,
    url="https://github.com/idemia/python-iso19794",
    packages = ['iso19794'],
    test_suite = 'iso19794.tests',
    install_requires = [
        'setuptools',
        'Pillow>=5.0.0'
        ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: CeCILL-C Free Software License Agreement (CECILL-C)",
        "Operating System :: OS Independent",
    ],
)
