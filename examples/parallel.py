#!/usr/bin/env python3
import argparse
import json
import sys
from typing import List
import asyncio

from aiohttp.client import ClientSession
import tqdm

from autoextract.aio import API_TIMEOUT, request_parallel, ApiError


async def main(urls: List[str], out, n_conn, batch_size, page_type='article'):
    async with ClientSession(timeout=API_TIMEOUT) as session:
        results_iter = request_parallel(urls,
                                        page_type=page_type,
                                        n_conn=n_conn,
                                        batch_size=batch_size,
                                        session=session)
        pbar = tqdm.tqdm(smoothing=0, leave=True, total=len(urls), miniters=1,
                         unit="url")
        for f in results_iter:
            try:
                batch_result = await f
                for res in batch_result:
                    json.dump(res, out, ensure_ascii=False)
                    out.write("\n")
                    out.flush()
                    pbar.update()
            except ApiError as e:
                print(e, file=sys.stderr)
                raise
        pbar.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("input",
                   type=argparse.FileType("r", encoding='utf8'),
                   help="input file with urls, one per line")
    p.add_argument("output",
                   type=argparse.FileType("w", encoding='utf8'),
                   help=".jsonlines file to store data")
    p.add_argument("--n-conn", type=int, default=20,
                   help="number of connections to the API server")
    p.add_argument("--batch-size", type=int, default=2,
                   help="batch size")
    p.add_argument("--page-type", default="article",
                   choices=['article', 'product'])
    args = p.parse_args()

    urls = [u.strip() for u in args.input.readlines() if u.strip()]
    print(f"Loaded {len(urls)} urls from {args.input.name}", file=sys.stderr)
    print(f"Running AutoExtract (connections: {args.n_conn}, "
          f"batch size: {args.batch_size}, page type: {args.page_type})")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(urls=urls,
                                 out=args.output,
                                 n_conn=args.n_conn,
                                 batch_size=args.batch_size,
                                 page_type=args.page_type))
    loop.close()
