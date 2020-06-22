# -*- coding: utf-8 -*-
from aiohttp import ClientResponseError


# FIXME: rename to RequestError (?)
class ApiError(ClientResponseError):
    """ Exception which is raised when Request-level error is returned.
    In contrast with ClientResponseError, it allows to inspect response
    content.
    https://doc.scrapinghub.com/autoextract.html#request-level
    """
    def __init__(self, *args, **kwargs):
        self.response_content = kwargs.pop("response_content")
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"ApiError: {self.status}, message={self.message}, " \
               f"headers={self.headers}, body={self.response_content}"


class QueryError(Exception):
    """ Exception which is raised when a Query-level error is returned.
    https://doc.scrapinghub.com/autoextract.html#query-level
    """
    def __init__(self, query: List, message: str):
        self.query = query
        self.message = message

    def __str__(self):
        return f"QueryError: query={self.query}, message={self.message}"
