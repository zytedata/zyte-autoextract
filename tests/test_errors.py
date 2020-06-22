# -*- coding: utf-8 -*-
from contextlib import suppress

import pytest

from autoextract.aio.errors import QueryError


def get_error_response(message):
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


def test_query_error():
    message = "Downloader error: http404"
    response = get_error_response(message)
    exc = QueryError(response["query"], response["error"])
    assert exc.query == response["query"]
    assert exc.message == response["error"]


@pytest.mark.parametrize("message, domain_occupied, retry_seconds", (
    ("Domain example.com is occupied, please retry in 23.5 seconds", "example.com", 23.5),
    ("domain example.net is occupied, please retry in 23.5 seconds", "example.net", 23.5),
    ("Domain example.com is occupied, please retry in 23 seconds", "example.com", 23),
    ("domain example.net is occupied, please retry in 23 seconds", "example.net", 23),
    ("Domain example.com is occupied, please retry in asd seconds", "example.com", ValueError),
    ("domain example.net is occupied, please retry in xyz seconds", "example.net", ValueError),
    ("domain example.net is occupied, please retry in  seconds", None, None),
    ("domain example.net is occupied, please retry in seconds", None, None),
    ("foo bar", None, None),
))
def test_domain_occupied_query_error(message, domain_occupied, retry_seconds):
    response = get_error_response(message)
    exc = QueryError(response["query"], response["error"])
    assert exc.query == response["query"]
    assert exc.message == response["error"]
    assert exc.domain_occupied == domain_occupied

    if isinstance(retry_seconds, type) and issubclass(retry_seconds, Exception):
        with pytest.raises(retry_seconds):
            exc.retry_seconds
    else:
        assert exc.retry_seconds == retry_seconds
