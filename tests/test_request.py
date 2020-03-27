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
