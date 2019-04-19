# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any, List

import requests

from .batching import record_order, build_query, restore_order
from .constants import API_ENDPOINT, API_TIMEOUT
from .apikey import get_apikey


def request_raw(query: List[Dict[str, Any]],
                api_key: Optional[str] = None,
                endpoint: str = API_ENDPOINT,
                ) -> List[Dict[str, Any]]:
    """ Send a request to ScrapingHub Developer API. Query is a list of
    dicts, as described in the API docs. """
    auth = (get_apikey(api_key), '')
    timeout = API_TIMEOUT + 60
    resp = requests.post(endpoint, json=query, auth=auth, timeout=timeout)
    # with open('resp.json', 'wb') as f:
    #     f.write(resp.content)
    # resp.raise_for_status()
    return resp.json()


def request_batch(urls: List[str],
                  page_type: str,
                  api_key: Optional[str] = None,
                  endpoint: str = API_ENDPOINT,
                  ) -> List[Dict]:
    """  """
    query = record_order(build_query(urls, page_type))
    results = request_raw(query, api_key=api_key, endpoint=endpoint)
    return restore_order(results)
