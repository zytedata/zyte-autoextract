# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Union, Optional
import attr


QueryDict = Dict[str, Any]


@attr.s
class Request:
    """
    A single request data for Zyte Automatic Extraction.
    See https://docs.zyte.com/automatic-extraction.html#requests

    Note that `articleBodyRaw` is set to false by default here; API itself
    defaults to true. Set `articleBodyRaw=None` to remove `articleBodyRaw`
    parameter from the request and use server default.

    You can override API params passing a dictionary with extra data using the
    `extra` argument. Note that it will overwrite any previous configuration
    made using standard attributes like `articleBodyRaw` and `fullHtml`.
    """
    url = attr.ib()  # type: str
    pageType = attr.ib()  # type: str

    meta = attr.ib(default=None)  # type: Optional[str]
    articleBodyRaw = attr.ib(default=False)  # type: Optional[bool]
    fullHtml = attr.ib(default=None)  # type: Optional[bool]

    extra = attr.ib(default=None)  # type: Optional[dict]

    def as_dict(self) -> QueryDict:
        d = attr.asdict(self)
        d.update(**self.extra or {})
        del d['extra']
        return {key: value for key, value in d.items() if value is not None}


Query = Union[List[Request], List[QueryDict]]


@attr.s
class ArticleRequest(Request):
    pageType = attr.ib(default='article')


@attr.s
class ProductRequest(Request):
    pageType = attr.ib(default='product')


@attr.s
class JobPostingRequest(Request):
    pageType = attr.ib(default='jobPosting')


def query_as_dict_list(query: Query) -> List[QueryDict]:
    return [
        request.as_dict() if isinstance(request, Request) else request
        for request in query
    ]
