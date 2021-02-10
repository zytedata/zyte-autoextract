# -*- coding: utf-8 -*-
"""
Synchronous Zyte Automatic Extraction API client.
"""

from typing import Optional, Dict, Any, List

import requests

from .batching import record_order, build_query, restore_order
from .constants import API_ENDPOINT, API_TIMEOUT
from .apikey import get_apikey
from .utils import user_agent
from .request import Query, query_as_dict_list


def request_raw(query: Query,
                api_key: Optional[str] = None,
                endpoint: str = API_ENDPOINT,
                ) -> List[Dict[str, Any]]:
    """ Send a request to the Zyte Automatic Extraction API.
    Query is a list of Request instances or of dicts, as described
    in the API docs (see https://docs.zyte.com/automatic-extraction.html).
    """
    auth = (get_apikey(api_key), '')
    timeout = API_TIMEOUT + 60
    headers = {'User-Agent': user_agent(requests)}
    resp = requests.post(
        endpoint,
        json=query_as_dict_list(query),
        auth=auth,
        headers=headers,
        timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()


def request_batch(urls: List[str],
                  page_type: str,
                  api_key: Optional[str] = None,
                  endpoint: str = API_ENDPOINT,
                  ) -> List[Dict]:
    query = record_order(build_query(urls, page_type))
    results = request_raw(query, api_key=api_key, endpoint=endpoint)
    return restore_order(results)
