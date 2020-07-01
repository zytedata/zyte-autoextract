# -*- coding: utf-8 -*-
import re
from typing import Optional

from aiohttp import ClientResponseError


class RequestError(ClientResponseError):
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

    DOMAIN_OCCUPIED_REGEX = re.compile(
        r".*domain (.+) is occupied, please retry in (.+) seconds.*",
        re.IGNORECASE
    )

    RETRIABLE_QUERY_ERROR_MESSAGES = {
        msg.lower().strip()
        for msg in [
            "query timed out",
            "Downloader error: No response (network5)",
            "Downloader error: http50",
            "Downloader error: GlobalTimeoutError",
            "Proxy error: banned",
            "Proxy error: internal_error",
            "Proxy error: nxdomain",
            "Proxy error: timeout",
            "Proxy error: ssl_tunnel_error",
            "Proxy error: msgtimeout",
            "Proxy error: econnrefused",
            # Retry errors for AutoExtract API dev server
            "Error making splash request: ServerDisconnectedError",
            "Error making splash request: ClientOSError: [Errno 32] Broken pipe",
        ]
    }

    def __init__(self, query: dict, message: str):
        self.query = query
        self.message = message

    def __str__(self):
        return f"QueryError: query={self.query}, message={self.message}"

    @property
    def retriable(self) -> bool:
        if self.domain_occupied:
            return True

        return self.message.lower() in self.RETRIABLE_QUERY_ERROR_MESSAGES

    @property
    def domain_occupied(self) -> Optional[str]:
        match = self.DOMAIN_OCCUPIED_REGEX.match(self.message)
        return match.group(1) if match else None

    @property
    def retry_seconds(self) -> Optional[float]:
        match = self.DOMAIN_OCCUPIED_REGEX.match(self.message)
        try:
            return float(match.group(2)) if match else None
        except ValueError:
            raise ValueError(
                f"Could not extract retry seconds "
                f"from Domain Occupied error message: {self.message}"
            )
