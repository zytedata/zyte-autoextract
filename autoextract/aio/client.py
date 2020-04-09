# -*- coding: utf-8 -*-
"""
aiohttp Scrapinghub AutoExtract API client.
"""
import asyncio
from typing import Optional, Dict, List, Iterator
from functools import partial
import time

import aiohttp

from autoextract.constants import API_ENDPOINT, API_TIMEOUT
from autoextract.apikey import get_apikey
from autoextract.utils import chunks, user_agent
from autoextract.request import Query, query_as_dict_list
from autoextract.stats import ResponseStats, AggStats
from .retry import autoextract_retry
from .errors import ApiError


AIO_API_TIMEOUT = aiohttp.ClientTimeout(total=API_TIMEOUT + 60,
                                        sock_read=API_TIMEOUT + 30,
                                        sock_connect=10)


def create_session(**kwargs) -> aiohttp.ClientSession:
    """ Create a session with parameters suited for AutoExtract """
    kwargs.setdefault('timeout', AIO_API_TIMEOUT)
    return aiohttp.ClientSession(**kwargs)


class Result(List[Dict]):
    retry_stats: Optional[Dict] = None
    response_stats: Optional[List[ResponseStats]] = None


async def request_raw(query: Query,
                      api_key: Optional[str] = None,
                      endpoint: str = API_ENDPOINT,
                      *,
                      handle_retries: bool = True,
                      session: Optional[aiohttp.ClientSession] = None,
                      agg_stats: AggStats = None,
                      ) -> Result:
    """ Send a request to Scrapinghub AutoExtract API.

    ``query`` is a list of dicts or Request objects, as
    described in the API docs
    (see https://doc.scrapinghub.com/autoextract.html).

    ``api_key`` is your AutoExtract API key. If not set, it is
    taken from SCRAPINGHUB_AUTOEXTRACT_KEY environment variable.

    ``session`` is an optional aiohttp.ClientSession object;
    use it to enable HTTP Keep-Alive.

    This function retries http 429 errors and network errors by default;
    this allows to handle server-side throttling properly.
    Use ``handle_retries=False`` if you want to disable this behavior
    (e.g. to implement it yourself).

    When handle_retries is True, this function can raise

    1) autoextract.errors.ApiError, if there is an error returned by the API
       which is not a throttling response (e.g. it can be raised for incorrect
       request).
    2) tenacity.RetryError, if a network-related error persists for
       a long time, over the allowed time period.

    Throttling errors are retried indefinitely when handle_retries is True.

    ``agg_stats`` argument allows to keep track of various stats; pass an
    ``AggStats`` instance, and it'll be updated.

    See :func:`request_parallel_as_completed` for a more high-level
    interface to send requests in parallel.
    """
    if agg_stats is None:
        agg_stats = AggStats()  # dummy stats, to simplify code
    post = _post_func(session)
    post_kwargs = dict(
        url=endpoint,
        json=query_as_dict_list(query),
        auth=aiohttp.BasicAuth(get_apikey(api_key)),
        headers={'User-Agent': user_agent(aiohttp)},
    )
    response_stats = []
    start_global = time.perf_counter()

    async def request():
        stats = ResponseStats.create(start_global)
        agg_stats.n_attempts += 1
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
                    raise ApiError(
                        request_info=resp.request_info,
                        history=resp.history,
                        status=resp.status,
                        message=resp.reason,
                        headers=resp.headers,
                        response_content=content
                    )
                # good response
                response = await resp.json()
                stats.record_read(agg_stats)
                return response
        except Exception as e:
            if not isinstance(e, ApiError):
                agg_stats.n_errors += 1
            raise
        finally:
            response_stats.append(stats)

    if handle_retries:
        request = autoextract_retry(request)

    try:
        result = await request()
    except Exception:
        agg_stats.n_fatal_errors += 1
        raise

    result = Result(result)
    result.response_stats = response_stats
    if handle_retries:
        result.retry_stats = request.retry.statistics  # type: ignore
    agg_stats.n_results += 1
    return result


def request_parallel_as_completed(query: Query,
                                  api_key: Optional[str] = None,
                                  *,
                                  endpoint: str = API_ENDPOINT,
                                  session: Optional[aiohttp.ClientSession] = None,
                                  batch_size=1,
                                  n_conn=1,
                                  agg_stats: AggStats = None,
                                  ) -> Iterator[asyncio.Future]:
    """ Send multiple requests to AutoExtract API in parallel.
    Return an `asyncio.as_completed` iterator.

    ``query`` is a list of requests to process (autoextract.Request
    instances or dicts).

    ``api_key`` is your AutoExtract API key. If not set, it is
    taken from SCRAPINGHUB_AUTOEXTRACT_KEY environment variable.

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
    """
    sem = asyncio.Semaphore(n_conn)

    async def _request(batch_query):
        async with sem:
            return await request_raw(batch_query,
                                     api_key=api_key,
                                     endpoint=endpoint,
                                     session=session,
                                     agg_stats=agg_stats)

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
