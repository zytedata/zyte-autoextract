# -*- coding: utf-8 -*-
import textwrap
from typing import Optional
import functools
import time

import attr
from runstats import Statistics


def zero_on_division_error(meth):
    @functools.wraps(meth)
    def wrapper(*args, **kwargs):
        try:
            return meth(*args, **kwargs)
        except ZeroDivisionError:
            return 0
    return wrapper


class AggStats:
    def __init__(self):
        self.time_connect_stats = Statistics()
        self.time_total_stats = Statistics()
        self.n_results = 0
        self.n_fatal_errors = 0

        self.n_attempts = 0
        self.n_429 = 0
        self.n_errors = 0

        self.n_input_queries = 0
        self.n_extracted_queries = 0  # Queries answered without any type of error
        self.n_query_responses = 0
        self.n_billable_query_responses = 0  # Some errors are also billed

    def __str__(self):
        return "conn:{:0.2f}s, resp:{:0.2f}s, throttle:{:.1%}, err:{}+{}({:.1%}) | success:{}/{}({:.1%})".format(
            self.time_connect_stats.mean(),
            self.time_total_stats.mean(),
            self.throttle_ratio(),
            self.n_errors - self.n_fatal_errors,
            self.n_fatal_errors,
            self.error_ratio(),
            self.n_extracted_queries,
            self.n_input_queries,
            self.success_ratio()
        )

    def summary(self):
        return textwrap.dedent(f"""
            Summary
            -------
            Mean connection time:    {self.time_connect_stats.mean():0.2f}
            Mean response time:      {self.time_total_stats.mean():0.2f}
            Throttle ratio:          {self.throttle_ratio():0.1%}
            Attempts:                {self.n_attempts}
            Errors:                  {self.error_ratio():0.1%}, fatal: {self.n_fatal_errors}, non fatal: {self.n_errors - self.n_fatal_errors}
            Successful URLs:         {self.n_extracted_queries} of {self.n_input_queries}
            Success ratio:           {self.success_ratio():0.1%}
            Billable query responses: {self.n_billable_query_responses} of {self.n_query_responses} 
        """)


    @zero_on_division_error
    def throttle_ratio(self):
        return self.n_429 / self.n_attempts

    @zero_on_division_error
    def error_ratio(self):
        return self.n_errors / self.n_attempts

    @zero_on_division_error
    def success_ratio(self):
        return self.n_extracted_queries / self.n_input_queries


@attr.s
class ResponseStats:
    _start = attr.ib(repr=False)  # type: float

    # Wait time, before this request is sent. Can be large in case of retries.
    time_delayed = attr.ib(default=None)  # type: Optional[float]

    # Time between sending a request and having a connection established
    time_connect = attr.ib(default=None)  # type: Optional[float]

    # Time to read & decode the response
    time_read = attr.ib(default=None)  # type: Optional[float]

    # Total time to process the response, excluding the wait time caused
    # by retries.
    time_total = attr.ib(default=None)  # type: Optional[float]

    # HTTP status code
    status = attr.ib(default=None)  # type: Optional[int]

    # response content, in case of error response
    error = attr.ib(default=None)  # type: Optional[bytes]

    @classmethod
    def create(cls, start_global):
        start = time.perf_counter()
        return cls(
            start=start,
            time_delayed=start - start_global,
        )

    def record_connected(self, agg_stats: AggStats):
        self.time_connect = time.perf_counter() - self._start
        agg_stats.time_connect_stats.push(self.time_connect)

    def record_read(self, agg_stats: Optional[AggStats]=None):
        now = time.perf_counter()
        self.time_total = now - self._start
        self.time_read = self.time_total - (self.time_connect or 0)
        if agg_stats:
            agg_stats.time_total_stats.push(self.time_total)
