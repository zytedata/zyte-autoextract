==========
python-xod
==========

.. image:: https://img.shields.io/pypi/v/xod.svg
   :target: https://pypi.python.org/pypi/xod
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/xod.svg
   :target: https://pypi.python.org/pypi/xod
   :alt: Supported Python Versions

.. image:: https://travis-ci.org/scrapinghub/python-xod.svg?branch=master
   :target: https://travis-ci.org/scrapinghub/python-xod
   :alt: Build Status

.. image:: https://codecov.io/github/scrapinghub/python-xod/coverage.svg?branch=master
   :target: https://codecov.io/gh/scrapinghub/python-xod
   :alt: Coverage report


Python client libraries for `Scrapinghub Developer API`_. It allows
to extract product and article information from any website.

Both synchronous and asyncio wrappers are provided by this package.

For Scrapy integration please check https://github.com/scrapinghub/scrapy-xod.

License is BSD 3-clause.

.. _Scrapinghub Developer API: https://scrapinghub.com/developer-api


Installation
============

::

    pip install xod

If you plan to use asyncio, run this instead, to install all dependencies::

    pip install xod[async]

python-xod requires Python 3.5+ for basic API and Python 3.6+ for async API.

Usage
=====

First, make sure you have an API key. To avoid passing it in ``api_key``
argument with every call, you can set ``SCRAPINGHUB_XOD_KEY`` environment
variable with the key.

Synchronous API
---------------

You can send requests as described in API docs::

    from xod.sync import request_raw
    query = [{'url': 'http://example.com.foo', 'pageType': 'article'}]
    results = request_raw(query)

Note that if there are several URLs in the query, results can be returned in
arbitrary order.

There is also a ``xod.sync.request_batch`` helper, which accepts URLs
and page type, and ensures results are in the same order as requested URLs::

    from xod.sync import request_batch
    urls = ['http://example.com/foo', 'http://example.com/bar']
    results = request_batch(urls, page_type='article')


asyncio API
-----------

Usage is similar to sync API (``request_batch`` and ``request_raw``
are available), but asyncio event loop is used::

    from xod.aio import request_raw, request_batch

    async def foo():
        results1 = await request_raw(query)
        results2 = await request_batch(urls, page_type='article')
        # ...


Contributing
============

* Source code: https://github.com/scrapinghub/python-xod
* Issue tracker: https://github.com/scrapinghub/python-xod/issues

Use tox_ to run tests with different Python versions::

    tox

The command above also runs type checks; we use mypy.

.. _tox: https://tox.readthedocs.io
