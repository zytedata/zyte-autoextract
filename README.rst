================
zyte-autoextract
================

.. image:: https://img.shields.io/pypi/v/zyte-autoextract.svg
   :target: https://pypi.python.org/pypi/zyte-autoextract
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/zyte-autoextract.svg
   :target: https://pypi.python.org/pypi/zyte-autoextract
   :alt: Supported Python Versions

.. image:: https://github.com/zytedata/zyte-autoextract/workflows/tox/badge.svg
   :target: https://github.com/zytedata/zyte-autoextract/actions
   :alt: Build Status

.. image:: https://codecov.io/github/zytedata/zyte-autoextract/coverage.svg?branch=master
   :target: https://codecov.io/gh/zytedata/zyte-autoextract
   :alt: Coverage report

Python client libraries for `Zyte Automatic Extraction API`_.
It allows to extract product, article, job posting, etc.
information from any website - whatever the API supports.

Command-line utility, asyncio-based library and a simple synchronous wrapper
are provided by this package.

License is BSD 3-clause.

.. _Zyte Automatic Extraction API: https://www.zyte.com/data-extraction/


Installation
============

::

    pip install zyte-autoextract

zyte-autoextract requires Python 3.6+ for CLI tool and for
the asyncio API; basic, synchronous API works with Python 3.5.

Usage
=====

First, make sure you have an API key. To avoid passing it in ``api_key``
argument with every call, you can set ``ZYTE_AUTOEXTRACT_KEY``
environment variable with the key.

Command-line interface
----------------------

The most basic way to use the client is from a command line.
First, create a file with urls, an URL per line (e.g. ``urls.txt``).
Second, set ``ZYTE_AUTOEXTRACT_KEY`` env variable with your
Zyte Automatic Extraction API key (you can also pass API key as ``--api-key`` script
argument).

Then run a script, to get the results::

    python -m autoextract urls.txt --page-type article --output res.jl

.. note::
    The results can be stored in an order which is different from the input
    order. If you need to match the output results to the input URLs, the
    best way is to use ``meta`` field (see below); it is passed through,
    and returned as-is in ``row["query"]["userQuery"]["meta"]``.

If you need more flexibility, you can customize the requests by creating
a JsonLines file with queries: a JSON object per line. You can pass any
Zyte Automatic Extraction options there. Example - store it in ``queries.jl`` file::

    {"url": "http://example.com", "meta": "id0", "articleBodyRaw": false}
    {"url": "http://example.com/foo", "meta": "id1", "articleBodyRaw": false}
    {"url": "http://example.com/bar", "meta": "id2", "articleBodyRaw": false}

See `API docs`_ for a description of all supported parameters in these query
dicts. API docs mention batch requests and their limitation
(no more than 100 queries at time); these limits don't apply to the queries.jl
file (i.e. it may have millions of rows), as the command-line script does
its own batching.

.. _API docs: https://docs.zyte.com/automatic-extraction.html

Note that in the example ``pageType`` argument is omitted; ``pageType``
values are filled automatically from ``--page-type`` command line argument
value. You can also set a different ``pageType`` for a row in ``queries.jl``
file; it has a priority over ``--page-type`` passed in cmdline.

To get results for this ``queries.jl`` file, run::

    python -m autoextract --intype jl queries.jl --page-type article --output res.jl

Processing speed
~~~~~~~~~~~~~~~~

Each API key has a limit on RPS. To get your URLs processed faster you can
tune concurrency options: batch size and a number of connections.

Best options depend on the RPS limit and on websites you're extracting
data from. For example, if your API key has a limit of 3RPS, and average
response time you observe for your websites is 10s, then to get to these
3RPS you may set e.g. batch size = 2, number of connections = 15 - this
would allow to process 30 requests in parallel.

To set these options in the CLI, use ``--n-conn`` and ``--batch-size``
arguments::

    python -m autoextract urls.txt --page-type articles --n-conn 15 --batch-size 2 --output res.jl

If too many requests are being processed in parallel, you'll be getting
throttling errors. They are handled by CLI automatically, but they make
extraction less efficient; please tune the concurrency options to
not hit the throttling errors (HTTP 429) often.

You may be also limited by the website speed. Zyte Automatic Extraction tries not to hit
any individual website too hard, but it could be better to limit this on
a client side as well. If you're extracting data from a single website,
it could make sense to decrease the amount of parallel requests; it can ensure
higher success ratio overall.

If you're extracting data from multiple websites, it makes sense to spread the
load across time: if you have websites A, B and C, don't send requests in
AAAABBBBCCCC order, send them in ABCABCABCABC order instead.

To do so, you can change the order of the queries in your input file.
Alternatively, you can pass ``--shuffle`` options; it randomly shuffles
input queries before sending them to the API:

    python -m autoextract urls.txt --shuffle --page-type articles --output res.jl

Run ``python -m autoextract --help`` to get description of all supported
options.

Errors
~~~~~~

The following errors could happen while making requests:

- Network errors
- `Request-level errors`_
    - Authentication failure
    - Malformed request
    - Too many queries in request
    - Request payload size is too large
- `Query-level errors`_
    - Downloader errors
    - Proxy errors
    - ...

Some errors can be retried while others can't.

For example,
you can retry a query with a Proxy Timeout error
because this is a temporary error
and there are chances that this response will be different
within the next retries.

On the other hand,
it makes no sense to retry queries that return a 404 Not Found error
because the response is not supposed to change if retried.

.. _Request-level errors: https://docs.zyte.com/automatic-extraction.html#request-level
.. _Query-level errors: https://docs.zyte.com/automatic-extraction.html#query-level

Retries
~~~~~~~

By default, we will automatically retry Network and Request-level errors.
You could also enable Query-level errors retries
by specifying the ``--max-query-error-retries`` argument.

Enable Query-level retries to increase the success rate
at the cost of more requests being performed
if you are interested in a higher success rate.

.. code-block::

    python -m autoextract urls.txt --page-type articles --max-query-error-retries 3 --output res.jl

Failing queries are retried
until the max number of retries or a timeout is reached.
If it's still not possible to fetch all queries without errors,
the last available result is written to the output
including both queries with success and the ones with errors.

Synchronous API
---------------

Synchronous API provides an easy way to try Zyte Automatic Extraction.
For production usage asyncio API is strongly recommended. Currently the
synchronous API doesn't handle throttling errors, and has other limitations;
it is most suited for quickly checking extraction results for a few URLs.

To send a request, use ``request_raw`` function; consult with the
`API docs`_ to understand how to populate the query::

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

.. note::
    Currently request_batch is limited to 100 URLs at time only.

asyncio API
-----------

Basic usage is similar to the sync API (``request_raw``),
but asyncio event loop is used::

    from autoextract.aio import request_raw

    async def foo():
        query = [{'url': 'http://example.com.foo', 'pageType': 'article'}]
        results1 = await request_raw(query)
        # ...

There is also ``request_parallel_as_completed`` function, which allows
to process many URLs in parallel, using both batching and multiple
connections::

    import sys
    from autoextract.aio import request_parallel_as_completed, create_session
    from autoextract import ArticleRequest

    async def extract_from(urls):
        requests = [ArticleRequest(url) for url in urls]
        async with create_session() as session:
            res_iter = request_parallel_as_completed(requests,
                                        n_conn=15, batch_size=2,
                                        session=session)
            for fut in res_iter:
                try:
                    batch_result = await fut
                    for res in batch_result:
                        # do something with a result, e.g.
                        print(json.dumps(res))
                except RequestError as e:
                    print(e, file=sys.stderr)
                    raise

``request_parallel_as_completed`` is modelled after ``asyncio.as_completed``
(see https://docs.python.org/3/library/asyncio-task.html#asyncio.as_completed),
and actually uses it under the hood.

Note ``from autoextract import ArticleRequest`` and its usage in the
example above. There are several Request helper classes,
which simplify building of the queries.

``request_parallel_as_completed`` and ``request_raw`` functions handle
throttling (http 429 errors) and network errors, retrying a request in
these cases.

CLI interface implementation (``autoextract/__main__.py``) can serve
as an usage example.

Request helpers
---------------

To query Zyte Automatic Extraction you need to create a dict with request parameters, e.g.::

    {'url': 'http://example.com.foo', 'pageType': 'article'}

To simplify the library usage and avoid typos, zyte-autoextract
provides helper classes for constructing these dicts::

* autoextract.Request
* autoextract.ArticleRequest
* autoextract.ProductRequest
* autoextract.JobPostingRequest

You can pass instances of these classes instead of dicts everywhere when
requests dicts are accepted. So e.g. instead of writing this::

    query = [{"url": url, "pageType": "article"} for url in urls]

You can write this::

    query = [Request(url, pageType="article") for url in urls]

or this::

    query = [ArticleRequest(url) for url in urls]

There is one difference: ``articleBodyRaw`` parameter is set to ``False``
by default when Request or its variants are used, while it is ``True``
by default in the API.

You can override API params passing a dictionary with extra data using the
``extra`` argument. Note that it will overwrite any previous configuration
made using standard attributes like ``articleBodyRaw`` and ``fullHtml``.

Extra parameters example::

    request = ArticleRequest(
        url=url,
        fullHtml=True,
        extra={
            "customField": "custom value",
            "fullHtml": False
        }
    )

This will generate a query that looks like this::

    {
        "url": url,
        "pageType": "article",
        "fullHtml": False,  # our extra parameter overrides the previous value
        "customField": "custom value"  # not a default param but defined even then
    }


Contributing
============

* Source code: https://github.com/zytedata/zyte-autoextract
* Issue tracker: https://github.com/zytedata/zyte-autoextract/issues

Use tox_ to run tests with different Python versions::

    tox

The command above also runs type checks; we use mypy.

.. _tox: https://tox.readthedocs.io
