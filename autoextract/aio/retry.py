# -*- coding: utf-8 -*-
"""
AutoExtract retrying logic.

TODO: add sync support; only autoextract.aio is supported at the moment.
"""
import asyncio
import logging

from aiohttp import client_exceptions
from tenacity import (
    wait_chain,
    wait_fixed,
    wait_random_exponential,
    wait_random,
    stop_after_delay,
    retry_if_exception,
    RetryCallState,
    RetryError,
    retry,
    before_sleep_log,
    after_log,
)
from tenacity.stop import stop_base, stop_never
from tenacity.wait import wait_base

from .errors import RequestError, QueryError, QueryRetryError


logger = logging.getLogger(__name__)


_NETWORK_ERRORS = (
    asyncio.TimeoutError,  # could happen while reading the response body
    client_exceptions.ClientResponseError,
    client_exceptions.ClientOSError,
    client_exceptions.ServerConnectionError,
    client_exceptions.ServerDisconnectedError,
    client_exceptions.ServerTimeoutError,
    client_exceptions.ClientPayloadError,
    client_exceptions.ClientConnectorSSLError,
)


def _is_network_error(exc: Exception) -> bool:
    if isinstance(exc, RequestError):
        # RequestError is ClientResponseError, which is in the
        # _NETWORK_ERRORS list, but it should be handled
        # separately.
        return False
    return isinstance(exc, _NETWORK_ERRORS)


def _is_throttling_error(exc: Exception) -> bool:
    return isinstance(exc, RequestError) and exc.status == 429


def _is_server_error(exc: Exception) -> bool:
    return isinstance(exc, RequestError) and exc.status >= 500


def _is_retriable_query_error(exc: Exception) -> bool:
    return isinstance(exc, QueryError) and exc.retriable


def _is_domain_occupied_query_error(exc: Exception) -> bool:
    return isinstance(exc, QueryError) and exc.domain_occupied is not None


autoextract_retry_condition = (
    retry_if_exception(_is_throttling_error) |
    retry_if_exception(_is_network_error) |
    retry_if_exception(_is_server_error) |
    retry_if_exception(_is_domain_occupied_query_error) |
    retry_if_exception(_is_retriable_query_error)
)


class autoextract_wait_strategy(wait_base):
    def __init__(self):
        # throttling
        self.throttling_wait = wait_chain(
            # always wait 20-40s first
            wait_fixed(20) + wait_random(0, 20),

            # wait 20-40s again
            wait_fixed(20) + wait_random(0, 20),

            # wait from 30 to 630s, with full jitter and exponentially
            # increasing max wait time
            wait_fixed(30) + wait_random_exponential(multiplier=1, max=600)
        )

        # connection errors, other client and server failures
        self.network_wait = (
            # wait from 3s to ~1m
            wait_random(3, 7) + wait_random_exponential(multiplier=1, max=55)
        )
        self.server_wait = self.network_wait
        self.retriable_wait = self.network_wait

    def __call__(self, retry_state: RetryCallState) -> float:
        exc = retry_state.outcome.exception()
        if _is_throttling_error(exc):
            return self.throttling_wait(retry_state=retry_state)
        elif _is_network_error(exc):
            return self.network_wait(retry_state=retry_state)
        elif _is_server_error(exc):
            return self.server_wait(retry_state=retry_state)
        elif _is_domain_occupied_query_error(exc):
            return exc.retry_seconds
        elif _is_retriable_query_error(exc):
            return max(
                exc.retry_seconds or 0,
                self.retriable_wait(retry_state=retry_state)
            )
        else:
            raise RuntimeError("Invalid retry state exception: %s" % exc)


class autoextract_stop_strategy(stop_base):
    def __init__(self):
        self.stop_on_throttling_error = stop_never
        self.stop_on_network_error = stop_after_delay(15 * 60)
        self.stop_on_server_error = self.stop_on_network_error
        self.stop_on_retriable_query_error = self.stop_on_network_error
        self.stop_on_domain_occupied_query_error = stop_never

    def __call__(self, retry_state: RetryCallState) -> bool:
        exc = retry_state.outcome.exception()
        if _is_throttling_error(exc):
            return self.stop_on_throttling_error(retry_state)
        elif _is_network_error(exc):
            return self.stop_on_network_error(retry_state)
        elif _is_server_error(exc):
            return self.stop_on_server_error(retry_state)
        elif _is_domain_occupied_query_error(exc):
            return self.stop_on_domain_occupied_query_error(retry_state)
        elif _is_retriable_query_error(exc):
            return self.stop_on_retriable_query_error(retry_state)
        else:
            raise RuntimeError("Invalid retry state exception: %s" % exc)


def _exception_factory(fut):
    exc = fut.exception()
    if isinstance(exc, QueryError):
        return QueryRetryError(fut)

    return RetryError(fut)


autoextract_retry = retry(
    wait=autoextract_wait_strategy(),
    retry=autoextract_retry_condition,
    stop=autoextract_stop_strategy(),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
    after=after_log(logger, logging.DEBUG),
    retry_error_cls=_exception_factory,
)
