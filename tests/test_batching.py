# -*- coding: utf-8 -*-
import copy

import pytest

from autoextract.batching import build_query, record_order

URLS = [
    'http://example.com',
    'https://foo.example.com/foo',
    'http://example.com/1'
]


def test_build_query():
    query = build_query(
        urls=['http://example.com', 'http://example.org'],
        page_type='article')
    assert query == [
        {'url': 'http://example.com', 'pageType': 'article'},
        {'url': 'http://example.org', 'pageType': 'article'},
    ]


def test_build_query_too_many():
    urls = URLS * 100
    with pytest.raises(ValueError):
        build_query(urls, "article")


def test_record_order():
    query = build_query(URLS, "article")
    query_old = copy.deepcopy(query)
    new_query = record_order(query)
    assert query == query_old
    assert [q['meta'] for q in new_query] == ['0', '1', '2']
    assert [q['url'] for q in new_query] == URLS
    assert [q['pageType'] for q in new_query] == ['article'] * len(URLS)
