# -*- coding: utf-8 -*-
""" Basic command-line interface for AutoExtract. """
import argparse
import json
import sys
from typing import List
import asyncio
import logging

import tqdm

from autoextract.aio import request_parallel, ApiError, create_session
from autoextract.constants import ENV_VARIABLE


logger = logging.getLogger('autoextract')


async def run(urls: List[str], out, n_conn, batch_size, page_type='article',
              api_key=None):
    async with create_session() as session:
        results_iter = request_parallel(urls,
                                        page_type=page_type,
                                        n_conn=n_conn,
                                        batch_size=batch_size,
                                        session=session,
                                        api_key=api_key)
        pbar = tqdm.tqdm(smoothing=0, leave=True, total=len(urls), miniters=1,
                         unit="url")
        try:
            for f in results_iter:
                try:
                    batch_result = await f
                    for res in batch_result:
                        json.dump(res, out, ensure_ascii=False)
                        out.write("\n")
                        out.flush()
                        pbar.update()
                except ApiError as e:
                    logger.error(str(e))
                    raise
        finally:
            pbar.close()


if __name__ == '__main__':
    """ Process urls from input file through AutoExtract """
    p = argparse.ArgumentParser(
        prog='python -m autoextract',
        description="""
        Process input URLs from a file using AutoExtract.
        """,
    )
    p.add_argument("input",
                   type=argparse.FileType("r", encoding='utf8'),
                   help="input file with urls, one url per line")
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
                   help="Scrapinghub AutoExtract API key. "
                        "You can also set %s environment variable instead "
                        "of using this option." % ENV_VARIABLE)
    p.add_argument("--loglevel", "-L", default="INFO",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                   help="log level")
    args = p.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel))

    urls = [u.strip() for u in args.input.readlines() if u.strip()]
    logger.info(f"Loaded {len(urls)} urls from {args.input.name}")
    logger.info(f"Running AutoExtract (connections: {args.n_conn}, "
                f"batch size: {args.batch_size}, page type: {args.page_type})")

    loop = asyncio.get_event_loop()
    coro = run(urls=urls,
               out=args.output,
               n_conn=args.n_conn,
               batch_size=args.batch_size,
               page_type=args.page_type,
               api_key=args.api_key)
    loop.run_until_complete(coro)
    loop.close()
