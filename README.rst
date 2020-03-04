========
iso19794
========

.. image:: https://readthedocs.org/projects/iso19794/badge/?version=latest
    :target: https://iso19794.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/l/iso19794.svg
    :target: https://pypi.org/project/iso19794/
    :alt: CeCILL-C

.. image:: https://img.shields.io/pypi/pyversions/iso19794.svg
    :target: https://pypi.org/project/iso19794/
    :alt: Python 3.x

.. image:: https://img.shields.io/pypi/v/iso19794.svg
    :target: https://pypi.org/project/iso19794/
    :alt: v?.?

.. image:: https://travis-ci.org/idemia/python-iso19794.svg?branch=master
    :target: https://travis-ci.org/idemia/python-iso19794
    :alt: Build Status (Travis CI)

.. image:: https://codecov.io/gh/idemia/python-iso19794/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/idemia/python-iso19794
    :alt: Code Coverage Status (Codecov)


A Python library extending Pillow to support ISO-19794 images.

Installation
============

``iso19794`` is published on PyPI and can be installed from there::

    pip install -U iso19794

Quick Start
===========

To open an ISO 19794 image:

.. code-block:: python

    from import Image
    import iso19794

    img = Image("my_image.fir")
    img = Image("my_image.fac")

