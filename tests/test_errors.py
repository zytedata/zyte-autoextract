# -*- coding: utf-8 -*-
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
    ("Domain example.com is occupied, please retry in asd seconds", "example.com", 300.0),
    ("domain example.net is occupied, please retry in xyz seconds", "example.net", 300.0),
    ("foo bar", None, None),
))
def test_domain_occupied_query_error(message, domain_occupied, retry_seconds):
    response = get_error_response(message)
    exc = QueryError(response["query"], response["error"])
    assert exc.query == response["query"]
    assert exc.message == response["error"]
    assert exc.domain_occupied == domain_occupied
    assert exc.retry_seconds == retry_seconds
