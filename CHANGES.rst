Changes
=======

0.7.0 (2021-02-10)
------------------

Update to accommodate upstream rebranding changes, as Scrapinghub has become
Zyte.

This update involves some major changes:

-   The repository name and the package name in the Python Package Index have
    changed from ``scrapinghub-autoextract`` to ``zyte-autoextract``.

-   The ``SCRAPINGHUB_AUTOEXTRACT_KEY`` environment variable has been renamed
    to ``ZYTE_AUTOEXTRACT_KEY``.

0.6.1 (2021-01-27)
------------------

* fixed ``max_retries`` behaviour. Total attempts must be max_retries + 1

0.6.0 (2020-12-29)
------------------

* CLI changes: error display in the progress bar is changed;
  summary is printed after the executions
* more errors are retried when retrying is enabled, which allows for a higher
  success rate
* fixed tcp connection pooling
* ``autoextract.aio.request_raw`` function allows to pass custom headers
  to the API (not to remote websites)
* ``autoextract.aio.request_raw`` now allows to customize the retry
  behavior, via ``retrying`` argument
* ``tenacity.RetryError`` is no longer raised by the library; concrete errors
  are raised instead
* Python 3.9 support
* CI is moved from Travis to Github Actions

0.5.2 (2020-11-27)
------------------

* ``QueryError`` is renamed to ``_QueryError``, as this is not an error
  users of the library ever see.
* Retrials were broken by having userAgent in the userQuery API output;
  temporary workaround is added to make retrials work again.

0.5.1 (2020-08-21)
------------------

* fix a problem that was preventing calls to ``request_raw`` when ``endpoint`` argument was ``None``

0.5.0 (2020-08-21)
------------------

* add ``--api-endpoint`` option to the command line utility
* improves documentation adding details about ``Request``'s extra parameters

0.4.0 (2020-08-17)
------------------

``autoextract.Request`` helper class now allows to set arbitrary
parameters for AutoExtract requests - they can be passed in ``extra`` argument.

0.3.0 (2020-07-24)
------------------

In this release retry-related features are added or improved.
It is now possible to fix some of the temporary errors
by enabling query-level retries, and the default retry behavior is improved.

* **backwards-incompatible**: autoextract.aio.ApiError is renamed
  to autoextract.aio.RequestError
* ``max_query_error_retries`` argument is added to
  ``autoextract.aio.request_raw`` and
  ``autoextract.aio.request_parallel_as_completed`` functions; it allows to
  enable retries of temporary query-level errors returned by the API.
* CLI: added ``--max-query-error-retries`` option to retry temporary
  query-level errors.
* HTTP 500 errors from server are retried now;
* documentation and test improvements.

0.2.0 (2020-04-15)
------------------

* asyncio API is rewritten, to simplify use in cases where passing meta
  is required. ``autoextract.aio.request_parallel_as_completed`` is added,
  ``autoextract.aio.request_parallel`` and ``autoextract.aio.request_batch``
  are removed.
* CLI: it now shows various stats: mean response and connect time,
  % of throttling errors, % of network and other errors
* CLI: new ``--intype jl`` option allows to process a .jl file
  with arbitrary AutoExtract API queries
* CLI: new ``--shuffle`` option allows to shuffle input data, to spread it
  more evenly across websites.
* CLI: it no longer exits on unrecoverable errors, to aid long-running
  processing tasks.
* retry logic is adjusted to handle network errors better.
* ``autoextract.aio.request_raw`` and
  ``autoextract.aio.request_parallel_as_completed`` functions provide an
  interface to return statistics about requests made, including retries.
* autoextract.Request, autoextract.ArticleRequest, autoextract.ProductRequest,
  autoextract.JobPostingRequest helper classes
* Documentation improvements.

0.1.1 (2020-03-12)
------------------

* allow up to 100 elements in a batch, not up to 99
* custom User-Agent header is added
* Python 3.8 support is declared & tested

0.1 (2019-10-09)
----------------

Initial release.
