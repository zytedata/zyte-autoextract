# -*- coding: utf-8 -*-
import logging
import re
from datetime import timedelta
from typing import Optional

from aiohttp import ClientResponseError


logger = logging.getLogger(__name__)


DOMAIN_OCCUPIED_REGEX = re.compile(
    r".*domain (.*) is occupied, please retry in (.*) seconds.*",
    re.IGNORECASE
)


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

    RETRY_MINUTES = 5

    def __init__(self, query: dict, message: str):
        self.query = query
        self.message = message

    def __str__(self):
        return f"QueryError: query={self.query}, message={self.message}"

    @property
    def domain_occupied(self) -> Optional[str]:
        match = DOMAIN_OCCUPIED_REGEX.match(self.message)
        return match and match.group(1)

    @property
    def retry_seconds(self):
        match = DOMAIN_OCCUPIED_REGEX.match(self.message)

        try:
            return match and float(match.group(2))
        except (TypeError, ValueError):
            logger.warning(
                f"Could not extract retry seconds "
                f"from Domain Occupied error message: {self.message}"
            )
            return timedelta(minutes=self.RETRY_MINUTES).total_seconds()
