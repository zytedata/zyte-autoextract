# -*- coding: utf-8 -*-
from aiohttp import ClientResponseError


class ApiError(ClientResponseError):
    """ Exception which is raised when API returns an error.
    In contrast with ClientResponseError, it allows to inspect response
    content.
    """
    def __init__(self, *args, **kwargs):
        self.response_content = kwargs.pop("response_content")
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"ApiError: {self.status}, message={self.message}, " \
               f"headers={self.headers}, body={self.response_content}"

