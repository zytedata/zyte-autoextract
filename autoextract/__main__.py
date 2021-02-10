# -*- coding: utf-8 -*-
""" Basic command-line interface for Zyte Automatic Extraction. """
import argparse
import json
import sys
import asyncio
import logging
import random

import tqdm

from autoextract import Request
from autoextract.aio import (
    request_parallel_as_completed,
    create_session
)
from autoextract.stats import AggStats
from autoextract.aio.client import Result
from autoextract.constants import ENV_VARIABLE
from autoextract.request import Query


logger = logging.getLogger('autoextract')


async def run(query: Query, out, n_conn, batch_size, stop_on_errors=False,
              api_key=None, api_endpoint=None, max_query_error_retries=0):
    agg_stats = AggStats()
    async with create_session(connection_pool_size=n_conn) as session:
        result_iter = request_parallel_as_completed(
            query=query,
            n_conn=n_conn,
            batch_size=batch_size,
            session=session,
            api_key=api_key,
            endpoint=api_endpoint,
            agg_stats=agg_stats,
            max_query_error_retries=max_query_error_retries
        )
        pbar = tqdm.tqdm(smoothing=0, leave=True, total=len(query), miniters=1,
                         unit="url")
        pbar.set_postfix_str(str(agg_stats))
        try:
            for fut in result_iter:
                try:
                    batch_result: Result = await fut
                    for res in batch_result:
                        json.dump(res, out, ensure_ascii=False)
                        out.write("\n")
                        out.flush()
                        pbar.update()
                except Exception as e:
                    if stop_on_errors:
                        raise
                    logger.error(str(e))
                finally:
                    pbar.set_postfix_str(str(agg_stats))
        finally:
            pbar.close()
    logger.info(agg_stats.summary())


def read_input(input_fp, intype, page_type):
    assert intype in {"txt", "jl", ""}
    if intype == "txt":
        urls = [u.strip() for u in input_fp.readlines() if u.strip()]
        query = [Request(url, pageType=page_type) for url in urls]
        return query
    elif intype == "jl":
        records = [
            json.loads(line.strip())
            for line in input_fp.readlines() if line.strip()
        ]
        for rec in records:
            rec.setdefault("pageType", page_type)
            if not isinstance(rec.get("meta", ""), (str, type(None))):
                raise TypeError("meta must be str or null, got {!r}".format(rec['meta']))
        return records


if __name__ == '__main__':
    """ Process urls from input file through Zyte Automatic Extraction """
    p = argparse.ArgumentParser(
        prog='python -m autoextract',
        description="""
        Process input URLs from a file using Zyte Automatic Extraction.
        """,
    )
    p.add_argument("input",
                   type=argparse.FileType("r", encoding='utf8'),
                   help="Input file with urls, url per line by default. The "
                        "Format can be changed using `--intype` argument.")
    p.add_argument("--intype", default="txt", choices=["txt", "jl"],
                   help='Type of the input file (default: %(default)s). '
                        'Allowed values are "txt": input should be one '
                        'URL per line, and "jl": input should be a jsonlines '
                        'file, with {"url": "...", "meta": ...,} dicts; see '
                        'https://docs.zyte.com/automatic-extraction.html#requests '
                        'for the data format description.')
    p.add_argument("--output", "-o",
                   default=sys.stdout,
                   type=argparse.FileType("w", encoding='utf8'),
                   help=".jsonlines file to store extracted data. "
                        "By default, results are printed to stdout.")
    p.add_argument("--n-conn", type=int, default=20,
                   help="number of connections to the API server "
                        "(default: %(default)s)")
    p.add_argument("--batch-size", type=int, default=2,
                   help="batch size (default: %(default)s)")
    p.add_argument("--page-type", "-t", default="article",
                   help="type of the pages in the input file, "
                        "e.g. article, product, jobPosting "
                        "(default: %(default)s)")
    p.add_argument("--api-key",
                   help="Zyte Automatic Extraction API key. "
                        "You can also set %s environment variable instead "
                        "of using this option." % ENV_VARIABLE)
    p.add_argument("--api-endpoint",
                   help="Zyte Automatic Extraction API endpoint.")
    p.add_argument("--loglevel", "-L", default="INFO",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                   help="log level")
    p.add_argument("--shuffle", help="Shuffle input URLs", action="store_true")
    p.add_argument("--max-query-error-retries", type=int, default=0,
                   help="Max number of Query-level error retries. "
                        "Enable Query-level error retries to increase the "
                        "success rate at the cost of more requests being "
                        "performed. It is recommended if you are interested "
                        "in a higher success rate.")
    args = p.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel))

    query = read_input(args.input, args.intype, args.page_type)
    if args.shuffle:
        random.shuffle(query)

    logger.info(f"Loaded {len(query)} urls from {args.input.name}; shuffled: {args.shuffle}")
    logger.info(f"Running Zyte Automatic Extraction (connections: {args.n_conn}, "
                f"batch size: {args.batch_size}, page type: {args.page_type})")

    loop = asyncio.get_event_loop()
    coro = run(query,
               out=args.output,
               n_conn=args.n_conn,
               batch_size=args.batch_size,
               stop_on_errors=False,
               api_key=args.api_key,
               api_endpoint=args.api_endpoint,
               max_query_error_retries=args.max_query_error_retries)
    loop.run_until_complete(coro)
    loop.close()
