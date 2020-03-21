# -*- coding: utf-8 -*-
"""
aiohttp Scrapinghub AutoExtract API client.
"""
import asyncio
from typing import Optional, Dict, Any, List, Iterator
from functools import partial

import aiohttp

from autoextract.batching import record_order, restore_order, build_query
from autoextract.constants import API_ENDPOINT, API_TIMEOUT
from autoextract.apikey import get_apikey
from autoextract.utils import chunks, user_agent
from .retry import autoextract_retry
from .errors import ApiError


AIO_API_TIMEOUT = aiohttp.ClientTimeout(total=API_TIMEOUT + 60,
                                        sock_read=API_TIMEOUT + 30,
                                        sock_connect=10)


def create_session(**kwargs) -> aiohttp.ClientSession:
    """ Create a session with parameters suited for AutoExtract """
    kwargs.setdefault('timeout', AIO_API_TIMEOUT)
    return aiohttp.ClientSession(**kwargs)


async def request_raw(query: List[Dict[str, Any]],
                      api_key: Optional[str] = None,
                      endpoint: str = API_ENDPOINT,
                      *,
                      handle_retries: bool = True,
                      session: Optional[aiohttp.ClientSession] = None
                      ) -> List[Dict]:
    """ Send a request to Scrapinghub AutoExtract API.

    ``query`` is a list of dicts, as described in the API docs
    (see https://doc.scrapinghub.com/autoextract.html).

    ``api_key`` is your AutoExtract API key. If not set, it is
    taken from SCRAPINGHUB_AUTOEXTRACT_KEY environment variable.

    ``session`` is an optional aiohttp.ClientSession object;
    use it to enable HTTP Keep-Alive.

    This function retries http 429 errors and network errors by default;
    this allows to handle server-side throttling properly.
    Use ``handle_retries=False`` if you want to disable this behavior
    (e.g. to implement it yourself).

    See :func:`request_parallel` for a more high-level interface to send
    requests in parallel.
    """
    auth = aiohttp.BasicAuth(get_apikey(api_key))
    headers = {'User-Agent': user_agent(aiohttp)}
    post = _post_func(session)

    async def request():
        async with post(endpoint, json=query, auth=auth, headers=headers) as resp:
            if resp.status >= 400:
                content = await resp.read()
                resp.release()
                raise ApiError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=resp.reason,
                    headers=resp.headers,
                    response_content=content
                )
            else:
                return await resp.json()

    if handle_retries:
        request = autoextract_retry(request)

    return await request()


def request_parallel(urls: List[str],
                     page_type: str,
                     api_key: Optional[str] = None,
                     endpoint: str = API_ENDPOINT,
                     *,
                     session: Optional[aiohttp.ClientSession] = None,
                     batch_size=1,
                     n_conn=1,
                     ) -> Iterator[asyncio.Future]:
    """ Send multiple requests to AutoExtract API in parallel.

    ``urls`` is a list of urls to process. All urls are assumed to be
    of type ``page_type`` (e.g. "article").

    ``api_key`` is your AutoExtract API key. If not set, it is
    taken from SCRAPINGHUB_AUTOEXTRACT_KEY environment variable.

    ``n_conn`` is a number of parallel connections to a server.
    ``batch_size`` is an amount of queries sent in a batch in each connection.
    Higher batch_size increase response time, but allows to achieve the same
    throughput with less connections to server.

    ``session`` is an optional aiohttp.ClientSession object;
    use it to enable HTTP Keep-Alive.
    """
    sem = asyncio.Semaphore(n_conn)

    async def _request(batch):
        async with sem:
            return await request_batch(
                urls=batch,
                page_type=page_type,
                api_key=api_key,
                endpoint=endpoint,
                session=session,
            )

    url_batches = chunks(urls, batch_size)
    return asyncio.as_completed([_request(batch) for batch in url_batches])


async def request_batch(urls: List[str],
                        page_type: str,
                        api_key: Optional[str] = None,
                        *,
                        endpoint: str = API_ENDPOINT,
                        handle_retries: bool = True,
                        session: Optional[aiohttp.ClientSession] = None
                        ) -> List[Dict]:
    """ Send a batch request """
    query = record_order(build_query(urls, page_type))
    results = await request_raw(query,
                                api_key=api_key,
                                endpoint=endpoint,
                                session=session,
                                handle_retries=handle_retries)
    return restore_order(results)


def _post_func(session):
    """ Return a function to send a POST request """
    if session is None:
        return partial(aiohttp.request,
                       method='POST',
                       timeout=AIO_API_TIMEOUT)
    else:
        return session.post
