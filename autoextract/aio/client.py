# -*- coding: utf-8 -*-
"""
aiohttp Zyte Automatic Extraction API client.
"""
import asyncio
import time
import warnings
from typing import Optional, Dict, List, Iterator
from functools import partial

import aiohttp
from aiohttp import TCPConnector
from tenacity import AsyncRetrying

from autoextract.constants import API_ENDPOINT, API_TIMEOUT
from autoextract.apikey import get_apikey
from autoextract.utils import chunks, user_agent
from autoextract.request import Query, query_as_dict_list
from autoextract.stats import ResponseStats, AggStats
from .retry import autoextract_retrying
from .errors import RequestError, _QueryError, is_billable_error_msg

AIO_API_TIMEOUT = aiohttp.ClientTimeout(total=API_TIMEOUT + 60,
                                        sock_read=API_TIMEOUT + 30,
                                        sock_connect=10)


def create_session(connection_pool_size=100, **kwargs) -> aiohttp.ClientSession:
    """ Create a session with parameters suited for Zyte Automatic Extraction """
    kwargs.setdefault('timeout', AIO_API_TIMEOUT)
    if "connector" not in kwargs:
        kwargs["connector"] = TCPConnector(limit=connection_pool_size)
    return aiohttp.ClientSession(**kwargs)


class Result(List[Dict]):
    retry_stats: Optional[Dict] = None
    response_stats: Optional[List[ResponseStats]] = None


class RequestProcessor:
    """Help keeping track of query results and errors between retries.

    After initializing your Request Processor,
    you may use it for just a single or for multiple requests.

    This class is especially useful because it stores
    successful queries to avoid repeating them when retrying requests.
    """

    def __init__(self, query: Query, max_retries: int = 0):
        """Reset temporary data structures and initialize them"""
        self._reset()
        self.pending_queries = query_as_dict_list(query)
        self._max_retries = max_retries
        self._complete_queries: List[Dict] = list()
        self._n_extracted_queries: int = 0
        self._n_query_responses: int = 0
        self._n_billable_query_responses: int = 0

    def _reset(self):
        """Clear temporary variables between retries"""
        self.pending_queries: List[Dict] = list()
        self._retriable_queries: List[Dict] = list()
        self._retriable_query_exceptions: List[Dict] = list()

    def _enqueue_error(self, query_result, query_exception):
        """Enqueue Query-level error.

        Enqueued errors could be:
            - used in combination with successes with `get_latest_results`
            - retried using `pending_requests`
        """
        self._retriable_queries.append(query_result)
        self._retriable_query_exceptions.append(query_exception)

        user_query = query_result["query"]["userQuery"]

        # Temporary workaround for a backend issue. Won't be needed soon.
        if 'userAgent' in user_query:
            del user_query['userAgent']

        self.pending_queries.append(user_query)

    def get_latest_results(self):
        """Get latest results (errors + successes).

        This method could be used to retrieve results
        when an exception is raised while processing results.
        """
        return self._complete_queries + self._retriable_queries

    def extracted_queries_count(self):
        """Number of queries extracted without any error"""
        return self._n_extracted_queries

    def query_responses_count(self):
        """Number of query responses received"""
        return self._n_query_responses

    def billable_query_responses_count(self):
        """Number of billable query responses (some errors are billable)"""
        return self._n_billable_query_responses

    def process_results(self, query_results):
        """Process query results.

        Return successful queries and also failed ones.

        If `self._max_retries` is greater than 0,
        this method might raise a `QueryError` exception.

        If multiple `QueryError` exceptions are parsed,
        the one with the longest timeout is raised.

        Successful requests are saved in `self._complete_queries`
        among with errors that cannot be retried,
        and they are kept between executions
        while retriable failures are saved in `self._retriable_queries`.

        Queries saved in `self._retriable_queries` are moved to
        `self.pending_queries` between executions.
        You can use the first or the n-th result:

            - You can get all queries successfully responded in the first try.
            - You can get all queries successfully in the n-th try.
            - You may stop with a partial number of successful queries.
        """
        self._reset()
        for query_result in query_results:
            self._n_query_responses += 1
            if "error" not in query_result:
                self._n_extracted_queries += 1
                self._n_billable_query_responses += 1
            else:
                if is_billable_error_msg(query_result["error"]):
                    self._n_billable_query_responses += 1
            if self._max_retries and "error" in query_result:
                query_exception = _QueryError.from_query_result(
                    query_result, self._max_retries)
                if query_exception.retriable:
                    self._enqueue_error(query_result, query_exception)
                    continue

            self._complete_queries.append(query_result)

        if self._retriable_query_exceptions:
            # Prioritize exceptions that have retry seconds defined
            # and get the one with the longest timeout value
            exception_with_longest_timeout = max(
                self._retriable_query_exceptions,
                key=lambda exc: exc.retry_seconds
            )
            raise exception_with_longest_timeout

        return self.get_latest_results()


async def request_raw(query: Query,
                      api_key: Optional[str] = None,
                      endpoint: Optional[str] = None,
                      *,
                      handle_retries: bool = True,
                      max_query_error_retries: int = 0,
                      session: Optional[aiohttp.ClientSession] = None,
                      agg_stats: AggStats = None,
                      headers: Optional[Dict[str, str]] = None,
                      retrying: Optional[AsyncRetrying] = None
                      ) -> Result:
    """ Send a request to Zyte Automatic Extraction API.

    ``query`` is a list of dicts or Request objects, as
    described in the API docs
    (see https://docs.zyte.com/automatic-extraction.html).

    ``api_key`` is your Zyte Automatic Extraction API key. If not set, it is
    taken from ZYTE_AUTOEXTRACT_KEY environment variable.

    ``session`` is an optional aiohttp.ClientSession object;
    use it to enable HTTP Keep-Alive and to control connection
    pool size.

    This function retries http 429 errors and network errors by default;
    this allows to handle server-side throttling properly.
    Use ``handle_retries=False`` if you want to disable this behavior
    (e.g. to implement it yourself).

    Among others, this function can raise autoextract.errors.RequestError,
    if there is a Request-level error returned by the API after all attempts
    were exhausted.

    Throttling errors are retried indefinitely when handle_retries is True.

    When ``handle_retries=True``, we could also retry Query-level errors.
    Use ``max_query_error_retries > 0`` if you want to to enable this behavior.

    ``agg_stats`` argument allows to keep track of various stats; pass an
    ``AggStats`` instance, and it'll be updated.

    Additional ``headers`` for the API request can be provided. This headers
    are included in the request done against the API endpoint: they
    won't be used in subsequent requests for fetching the URLs provided in
    the query.

    The default retry policy can be overridden by providing a custom
    ``retrying`` object of type :class:`tenacity.AsyncRetrying` that can
    be built with the class :class:`autoextract.retry.RetryFactory`.
    The following is an example that configure 3 attempts for server
    type errors::

      factory = RetryFactory()
      factory.server_error_stop = stop_after_attempt(3)
      retrying = factory.build()

    See :func:`request_parallel_as_completed` for a more high-level
    interface to send requests in parallel.
    """
    endpoint = API_ENDPOINT if endpoint is None else endpoint
    retrying = retrying or autoextract_retrying

    if agg_stats is None:
        agg_stats = AggStats()  # dummy stats, to simplify code

    if max_query_error_retries and not handle_retries:
        warnings.warn(
            "You've specified a max number of Query-level error retries, "
            "but retries are disabled. Consider passing the handle_retries "
            "argument as True.",
            stacklevel=2
        )

    # Keep state between executions/retries
    request_processor = RequestProcessor(
        query=query,
        max_retries=max_query_error_retries if handle_retries else 0,
    )

    post = _post_func(session)
    auth = aiohttp.BasicAuth(get_apikey(api_key))
    headers = {'User-Agent': user_agent(aiohttp), **(headers or {})}

    response_stats = []
    start_global = time.perf_counter()

    async def request():
        stats = ResponseStats.create(start_global)
        agg_stats.n_attempts += 1

        post_kwargs = dict(
            url=endpoint,
            json=request_processor.pending_queries,
            auth=auth,
            headers=headers,
        )

        try:
            async with post(**post_kwargs) as resp:
                stats.status = resp.status
                stats.record_connected(agg_stats)
                if resp.status >= 400:
                    content = await resp.read()
                    resp.release()
                    stats.record_read()
                    stats.error = content
                    if resp.status == 429:
                        agg_stats.n_429 += 1
                    else:
                        agg_stats.n_errors += 1
                    raise RequestError(
                        request_info=resp.request_info,
                        history=resp.history,
                        status=resp.status,
                        message=resp.reason,
                        headers=resp.headers,
                        response_content=content
                    )

                response = await resp.json()
                stats.record_read(agg_stats)
                return request_processor.process_results(response)
        except Exception as e:
            if not isinstance(e, RequestError):
                agg_stats.n_errors += 1
            raise
        finally:
            response_stats.append(stats)

    if handle_retries:
        request = retrying.wraps(request)

    try:
        # Try to make a batch request
        result = await request()
    except _QueryError:
        # If Tenacity fails to retry a _QueryError because the max number of
        # retries or a timeout was reached, get latest results combining
        # error and successes and consider it as the final result.
        result = request_processor.get_latest_results()
    except Exception:
        agg_stats.n_fatal_errors += 1
        raise
    finally:
        agg_stats.n_input_queries += len(query)
        agg_stats.n_extracted_queries += request_processor.extracted_queries_count()
        agg_stats.n_billable_query_responses += request_processor.billable_query_responses_count()
        agg_stats.n_query_responses += request_processor.query_responses_count()

    result = Result(result)
    result.response_stats = response_stats
    if handle_retries and hasattr(request, 'retry'):
        result.retry_stats = request.retry.statistics  # type: ignore

    agg_stats.n_results += 1
    return result


def request_parallel_as_completed(query: Query,
                                  api_key: Optional[str] = None,
                                  *,
                                  endpoint: Optional[str] = None,
                                  session: Optional[aiohttp.ClientSession] = None,
                                  batch_size=1,
                                  n_conn=1,
                                  agg_stats: AggStats = None,
                                  max_query_error_retries=0,
                                  ) -> Iterator[asyncio.Future]:
    """ Send multiple requests to Zyte Automatic Extraction API in parallel.
    Return an `asyncio.as_completed` iterator.

    ``query`` is a list of requests to process (autoextract.Request
    instances or dicts).

    ``api_key`` is your Zyte Automatic Extraction API key. If not set, it is
    taken from ZYTE_AUTOEXTRACT_KEY environment variable.

    ``n_conn`` is a number of parallel connections to a server.
    ``batch_size`` is an amount of queries sent in a batch in each connection.
    Higher batch_size increase response time, but allows to achieve the same
    throughput with less connections to server.

    For example, if your API key has a limit of 3RPS, and average response
    time you observe for your websites is 10s, then to get to these
    3RPS you may set e.g. batch_size=2, n_conn=15 - this would allow to
    process 30 requests in parallel.

    ``session`` is an optional aiohttp.ClientSession object;
    use it to enable HTTP Keep-Alive.

    ``agg_stats`` argument allows to keep track of various stats; pass an
    ``AggStats`` instance, and it'll be updated.

    Use ``max_query_error_retries > 0`` if you want Query-level
    errors to be retried.
    """
    sem = asyncio.Semaphore(n_conn)

    async def _request(batch_query):
        async with sem:
            return await request_raw(batch_query,
                                     api_key=api_key,
                                     endpoint=endpoint,
                                     session=session,
                                     agg_stats=agg_stats,
                                     max_query_error_retries=max_query_error_retries,
                                     )

    batches = chunks(query, batch_size)
    return asyncio.as_completed([_request(batch) for batch in batches])


def _post_func(session):
    """ Return a function to send a POST request """
    if session is None:
        return partial(aiohttp.request,
                       method='POST',
                       timeout=AIO_API_TIMEOUT)
    else:
        return session.post
