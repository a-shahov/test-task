import asyncio
import argparse
import logging

import aiohttp

from .const import ARCHITECTURES, URL, TIMEOUT

log = logging.getLogger()


async def _query(branch, arch, timeout):
    session_timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=session_timeout) as session:

        async with session.get(URL.format(branch),
                               params={'arch': arch}) as resp:

            return (resp.status, await resp.text())


async def query_bins(arch, timeout):
    queries = [asyncio.create_task(_query('p10', arch, timeout)),
               asyncio.create_task(_query('sisyphus', arch, timeout))]

    responses = await asyncio.gather(*queries, return_exceptions=True)

    if any(map(lambda value: isinstance(value, asyncio.TimeoutError), responses)):
        log.error('Timeout error during request execution. Use --timeout option')
        exit(1)

    if any(map(lambda value: value[0] != 200, responses)):
        log.error('Error when making a request')
        exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'arch',
        choices=ARCHITECTURES,
        help='arch is desired architecture.',
    )
    parser.add_argument(
        '--timeout',
        help=f'timeout for making request. default is {TIMEOUT}s',
        default=TIMEOUT,
        type=float,
    )
    args = parser.parse_args()

    asyncio.run(query_bins(args.arch, args.timeout))


if __name__ == '__main__':
    main()
