# -*- coding: utf-8 -*-
import pytest

from autoextract.aio.errors import _QueryError


def get_query_error(message):
    return {
        "query": {
            "id": "1587642195276-9386233af6ce1b9f",
            "domain": "example.com",
            "userQuery": {
                "url": "http://www.example.com/this-page-does-not-exist",
                "pageType": "article"
            },
        },
        "error": message,
    }


@pytest.mark.parametrize("message, retriable", (
        ("Downloader error: http404", False),
        ("query timed out", True),
        ("Downloader error: No response (network5)", True),
        ("Downloader error: http50", True),
        ("Downloader error: GlobalTimeoutError", True),
        ("Proxy error: banned", True),
        ("Proxy error: internal_error", True),
        ("Proxy error: nxdomain", True),
        ("Proxy error: timeout", True),
        ("Proxy error: ssl_tunnel_error", True),
        ("Proxy error: msgtimeout", True),
        ("Proxy error: econnrefused", True),
))
def test_query_error(message, retriable):
    query_error = get_query_error(message)

    exc = _QueryError.from_query_result(query_error)
    assert exc.query == query_error["query"]
    assert exc.message == query_error["error"]
    assert exc.retriable is retriable
    assert exc.domain_occupied is None
    assert str(exc) == f"_QueryError: query={exc.query}, message={exc.message}, max_retries={exc.max_retries}"

    exc = _QueryError(query=query_error["query"], message=query_error["error"])
    assert exc.query == query_error["query"]
    assert exc.message == query_error["error"]
    assert exc.retriable is retriable
    assert exc.domain_occupied is None
    assert str(exc) == f"_QueryError: query={exc.query}, message={exc.message}, max_retries={exc.max_retries}"


@pytest.mark.parametrize("message, domain, retry_seconds", (
    ("Domain example.com is occupied, please retry in 23.5 seconds", "example.com", 23.5),
    ("domain example.net is occupied, please retry in 23.5 seconds", "example.net", 23.5),
    ("Domain example.com is occupied, please retry in 23 seconds", "example.com", 23),
    ("domain example.net is occupied, please retry in 23 seconds", "example.net", 23),
    ("Domain example.com is occupied, please retry in asd seconds", "example.com", 300),  # 5 minutes default
    ("domain example.net is occupied, please retry in xyz seconds", "example.net", 300),  # 5 minutes default
))
def test_domain_occupied_query_error(message, domain, retry_seconds):
    query_error = get_query_error(message)
    exc = _QueryError.from_query_result(query_error)
    assert exc.domain_occupied.domain == domain
    assert exc.domain_occupied.retry_seconds == retry_seconds
    assert exc.retry_seconds == retry_seconds
    assert exc.retriable is True


@pytest.mark.parametrize("message", (
    "domain example.net is occupied, please retry in  seconds",
    "domain example.net is occupied, please retry in seconds",
    "foo bar",
))
def test_invalid_domain_occupied_query_error(message):
    query_error = get_query_error(message)
    exc = _QueryError.from_query_result(query_error)
    assert exc.domain_occupied is None
    assert exc.retry_seconds == 0.0
