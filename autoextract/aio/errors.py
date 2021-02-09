# -*- coding: utf-8 -*-
import json
import logging
import re
from json import JSONDecodeError
from typing import Optional

from aiohttp import ClientResponseError

logger = logging.getLogger(__name__)


class DomainOccupied:

    DOMAIN_OCCUPIED_REGEX = re.compile(
        r".*domain (.+) is occupied, please retry in (.+) seconds.*",
        re.IGNORECASE
    )

    DEFAULT_RETRY_SECONDS = 5 * 60  # 5 minutes

    def __init__(self, domain: str, retry_seconds: float):
        self.domain = domain
        self.retry_seconds = retry_seconds

    @classmethod
    def from_message(cls, message: str) -> Optional["DomainOccupied"]:
        match = cls.DOMAIN_OCCUPIED_REGEX.match(message)
        if not match:
            return None

        domain = match.group(1)

        try:
            retry_seconds = float(match.group(2))
        except ValueError:
            logger.warning(
                f"Could not extract retry seconds "
                f"from Domain Occupied error message: {message}"
            )
            retry_seconds = cls.DEFAULT_RETRY_SECONDS

        return cls(domain=domain, retry_seconds=retry_seconds)


class RequestError(ClientResponseError):
    """ Exception which is raised when Request-level error is returned.
    In contrast with ClientResponseError, it allows to inspect response
    content.
    https://docs.zyte.com/automatic-extraction.html#request-level
    """
    def __init__(self, *args, **kwargs):
        self.response_content = kwargs.pop("response_content")
        super().__init__(*args, **kwargs)

    def error_data(self):
        """
        Parses request error ``response_content``
        """
        data = {}
        if self.response_content:
            try:
                data = json.loads(self.response_content.decode("utf-8"))
                if not isinstance(data, dict):
                    data = {}
                    logger.warning(
                        "Wrong JSON format for RequestError content '{}'. "
                        "A dict was expected".format(self.response_content)
                    )
            except (JSONDecodeError, UnicodeDecodeError) as _:  # noqa: F841
                logger.warning(
                    "Wrong JSON format for RequestError content '{}'".format(
                        self.response_content)
                )
        return data

    def __str__(self):
        return f"RequestError: {self.status}, message={self.message}, " \
               f"headers={self.headers}, body={self.response_content}"


_RETRIABLE_ERR_MSGS = [
    "query timed out",
    "Downloader error: No response",
    "Downloader error: http50",
    "Downloader error: 50",
    "Downloader error: GlobalTimeoutError",
    "Downloader error: ConnectionResetByPeer",
    "Proxy error: banned",
    "Proxy error: internal_error",
    "Proxy error: nxdomain",
    "Proxy error: timeout",
    "Proxy error: ssl_tunnel_error",
    "Proxy error: msgtimeout",
    "Proxy error: econnrefused",
    "Proxy error: connect_timeout",
]


_RETRIABLE_ERR_MSGS_RE = re.compile(
    "|".join(re.escape(msg) for msg in _RETRIABLE_ERR_MSGS), re.IGNORECASE
)


def is_retriable_error_msg(msg: Optional[str]) -> bool:
    """True if the error is one of those that could benefit from a retry"""
    msg = msg or ""
    return bool(_RETRIABLE_ERR_MSGS_RE.search(msg))


class _QueryError(Exception):
    """ Exception which is raised when a Query-level error is returned.
    https://docs.zyte.com/automatic-extraction.html#query-level
    """

    def __init__(self, query: dict, message: str, max_retries: int = 0):
        self.query = query
        self.message = message
        self.max_retries = max_retries
        self.domain_occupied = DomainOccupied.from_message(message)

    def __str__(self):
        return f"_QueryError: query={self.query}, message={self.message}, " \
               f"max_retries={self.max_retries}"

    @classmethod
    def from_query_result(cls, query_result: dict, max_retries: int = 0):
        return cls(query=query_result["query"], message=query_result["error"],
                   max_retries=max_retries)

    @property
    def retriable(self) -> bool:
        if self.domain_occupied:
            return True
        return is_retriable_error_msg(self.message)

    @property
    def retry_seconds(self) -> float:
        if self.domain_occupied:
            return self.domain_occupied.retry_seconds
        return 0.0


# Based on https://docs.zyte.com/automatic-extraction.html#reference
_NON_BILLABLE_ERR_MSGS = [
    "malformed url",
    "URL cannot be longer than",
    "non-HTTP schemas are not allowed",
    "Extraction not permitted for this URL",
]


_NON_BILLABLE_ERR_MSGS_RE = re.compile(
    "|".join(re.escape(msg) for msg in _NON_BILLABLE_ERR_MSGS), re.IGNORECASE
)


def is_billable_error_msg(msg: Optional[str]) -> bool:
    """
    Return true if the error message is billable. Based on
    https://docs.zyte.com/automatic-extraction.html#reference

    >>> is_billable_error_msg(None)
    True
    >>> is_billable_error_msg("")
    True
    >>> is_billable_error_msg(" URL cannot be longer than 4096 UTF-16 characters ")
    False
    >>> is_billable_error_msg(" malformed url ")
    False
    >>> is_billable_error_msg("Domain example.com is occupied, please retry in 23.5 seconds")
    False
    """
    msg = msg or ""
    is_domain_ocupied = bool(DomainOccupied.from_message(msg))
    is_no_billable = (_NON_BILLABLE_ERR_MSGS_RE.search(msg) or
                      is_domain_ocupied)
    return not is_no_billable


ACCOUNT_DISABLED_ERROR_TYPE = "http://errors.xod.scrapinghub.com/account-disabled.html"