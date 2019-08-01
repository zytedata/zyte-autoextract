# -*- coding: utf-8 -*-
"""
aiohttp Scrapinghub AutoExtract API client.
"""
from typing import Optional, Dict, Any, List
from functools import partial

import aiohttp

from .batching import record_order, restore_order, build_query
from .constants import API_ENDPOINT, API_TIMEOUT
from .apikey import get_apikey


API_TIMEOUT = aiohttp.ClientTimeout(total=API_TIMEOUT + 60,
                                    sock_read=API_TIMEOUT + 30,
                                    sock_connect=10)


async def request_raw(query: List[Dict[str, Any]],
                      api_key: Optional[str] = None,
                      endpoint: str = API_ENDPOINT,
                      *,
                      session: Optional[aiohttp.ClientSession] = None
                      ) -> List[Dict]:
    """ Send a request to Scrapinghub AutoExtract API.
    Query is a list of dicts, as described in the API docs
    (see https://doc.scrapinghub.com/autoextract.html).
    """
    auth = aiohttp.BasicAuth(get_apikey(api_key))
    post = _post_func(session)
    async with post(endpoint, json=query, auth=auth) as resp:
        resp.raise_for_status()
        return await resp.json()


async def request_batch(urls: List[str],
                        page_type: str,
                        api_key: Optional[str] = None,
                        endpoint: str = API_ENDPOINT,
                        *,
                        session: Optional[aiohttp.ClientSession] = None
                        ) -> List[Dict]:
    # TODO: client-side batching? concurrency?
    query = record_order(build_query(urls, page_type))
    results = await request_raw(query,
                                api_key=api_key,
                                endpoint=endpoint,
                                session=session)
    return restore_order(results)


def _post_func(session):
    """ Return a function to send a POST request """
    if session is None:
        return partial(aiohttp.request, 'POST')
    else:
        return session.post
