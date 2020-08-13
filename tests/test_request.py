# -*- coding: utf-8 -*-
import pytest
from autoextract.request import (
    Request,
    ArticleRequest,
    ProductRequest,
    JobPostingRequest
)


def test_request():
    assert Request("http://example.com", pageType="foobar").as_dict() == {
        'url': 'http://example.com',
        'pageType': 'foobar',
        'articleBodyRaw': False,
    }


@pytest.mark.parametrize("cls,page_type", [
    [ArticleRequest, "article"],
    [ProductRequest, "product"],
    [JobPostingRequest, "jobPosting"]
])
def test_request_types(cls, page_type):
    req = cls("http://example.com")
    qdict = req.as_dict()
    assert qdict['pageType'] == page_type


def test_request_as_dict():
    request = Request("example.com", "myPageType")
    assert request.url == "example.com"
    assert request.pageType == "myPageType"
    assert request.fullHtml is None
    assert request.as_dict() == {
        'url': 'example.com',
        'pageType': 'myPageType',
        'articleBodyRaw': False,
    }

    request = Request("example.com", "myPageType", fullHtml=True)
    assert request.fullHtml is True
    assert request.as_dict() == {
        'url': 'example.com',
        'pageType': 'myPageType',
        'fullHtml': True,
        'articleBodyRaw': False,
    }

    request = Request("example.com", "myPageType", meta='foo bar', extra=dict(foo="bar"))
    assert request.url == "example.com"
    assert request.pageType == "myPageType"
    assert request.fullHtml is None
    assert request.as_dict() == {
        'url': 'example.com',
        'pageType': 'myPageType',
        'articleBodyRaw': False,
        'meta': 'foo bar',
        'foo': 'bar',
    }
