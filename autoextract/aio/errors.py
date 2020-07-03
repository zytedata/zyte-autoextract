# -*- coding: utf-8 -*-
import logging
import re
from typing import Optional

from aiohttp import ClientResponseError

logger = logging.getLogger(__name__)


class DomainOccupied:

    DOMAIN_OCCUPIED_REGEX = re.compile(
        r".*domain (.+) is occupied, please retry in (.+) seconds.*",
        re.IGNORECASE
    )

    def __init__(self, domain: str, retry_seconds: float):
        self.domain = domain
        self.retry_seconds = retry_seconds

    @classmethod
    def from_message(cls, message: str):
        match = cls.DOMAIN_OCCUPIED_REGEX.match(message)
        if not match:
            return

        domain = match.group(1)
        retry_seconds = match.group(2)

        try:
            retry_seconds = float(retry_seconds)
        except ValueError:
            logger.warning(
                f"Could not extract retry seconds "
                f"from Domain Occupied error message: {message}"
            )
            retry_seconds = 5 * 60  # 5 minutes

        return cls(domain=domain, retry_seconds=retry_seconds)


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

    RETRIABLE_MESSAGES = {
        message.lower().strip()
        for message in [
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
        self.domain_occupied = DomainOccupied.from_message(message)

    def __str__(self):
        return f"QueryError: query={self.query}, message={self.message}"

    @classmethod
    def from_query_result(cls, query_result: dict):
        return cls(query=query_result["query"], message=query_result["error"])

    @property
    def retriable(self) -> bool:
        if self.domain_occupied:
            return True

        return self.message.lower().strip() in self.RETRIABLE_MESSAGES

    @property
    def retry_seconds(self) -> Optional[float]:
        if self.domain_occupied:
            return self.domain_occupied.retry_seconds
