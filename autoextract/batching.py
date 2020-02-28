# -*- coding: utf-8 -*-
""" Helpers for batching requests """
from copy import deepcopy
from typing import List, Dict

from .constants import API_MAX_BATCH


def build_query(urls: List[str], page_type: str) -> List[Dict]:
    """ Given a list of URLs and page type, return query """
    if len(urls) > API_MAX_BATCH:
        raise ValueError("Batch size can't be greater than %s" %
                         API_MAX_BATCH)
    return [{'url': url, 'pageType': page_type} for url in urls]


def record_order(query: List[Dict]) -> List[Dict]:
    query = deepcopy(query)
    for idx, q in enumerate(query):
        assert 'meta' not in q
        q['meta'] = str(idx)
    return query


def restore_order(results: List[Dict]) -> List[Dict]:
    return sorted(results, key=_sort_key)


def _sort_key(row):
    return int(row['query']['userQuery']['meta'])
