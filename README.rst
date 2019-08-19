=======================
scrapinghub-autoextract
=======================

.. image:: https://img.shields.io/pypi/v/scrapinghub-autoextract.svg
   :target: https://pypi.python.org/pypi/scrapinghub-autoextract
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/scrapinghub-autoextract.svg
   :target: https://pypi.python.org/pypi/scrapinghub-autoextract
   :alt: Supported Python Versions

.. image:: https://travis-ci.org/scrapinghub/scrapinghub-autoextract.svg?branch=master
   :target: https://travis-ci.org/scrapinghub/scrapinghub-autoextract
   :alt: Build Status

.. image:: https://codecov.io/github/scrapinghub/scrapinghub-autoextract/coverage.svg?branch=master
   :target: https://codecov.io/gh/scrapinghub/scrapinghub-autoextract
   :alt: Coverage report


Python client libraries for `Scrapinghub AutoExtract API`_.
It allows to extract product and article information from any website.

Both synchronous and asyncio wrappers are provided by this package.

License is BSD 3-clause.

.. _Scrapinghub AutoExtract API: https://scrapinghub.com/autoextract


Installation
============

::

    pip install scrapinghub-autoextract

If you plan to use asyncio, run this instead, to install all dependencies::

    pip install scrapinghub-autoextract[async]

scrapinghub-autoextract requires Python 3.5+ for basic API
and Python 3.6+ for async API.

Usage
=====

First, make sure you have an API key. To avoid passing it in ``api_key``
argument with every call, you can set ``SCRAPINGHUB_AUTOEXTRACT_KEY``
environment variable with the key.

Synchronous API
---------------

You can send requests as described in `API docs`_::

    from autoextract.sync import request_raw
    query = [{'url': 'http://example.com.foo', 'pageType': 'article'}]
    results = request_raw(query)

Note that if there are several URLs in the query, results can be returned in
arbitrary order.

There is also a ``autoextract.sync.request_batch`` helper, which accepts URLs
and page type, and ensures results are in the same order as requested URLs::

    from autoextract.sync import request_batch
    urls = ['http://example.com/foo', 'http://example.com/bar']
    results = request_batch(urls, page_type='article')

.. _API docs: https://doc.scrapinghub.com/autoextract.html


asyncio API
-----------

Usage is similar to sync API (``request_batch`` and ``request_raw``
are available), but asyncio event loop is used::

    from autoextract.aio import request_raw, request_batch

    async def foo():
        results1 = await request_raw(query)
        results2 = await request_batch(urls, page_type='article')
        # ...


Contributing
============

* Source code: https://github.com/scrapinghub/scrapinghub-autoextract
* Issue tracker: https://github.com/scrapinghub/scrapinghub-autoextract/issues

Use tox_ to run tests with different Python versions::

    tox

The command above also runs type checks; we use mypy.

.. _tox: https://tox.readthedocs.io
