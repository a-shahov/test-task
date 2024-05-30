import asyncio
import argparse
import logging
import json
import re
from contextlib import suppress

import aiohttp

from .const import ARCHITECTURES, URL, TIMEOUT

log = logging.getLogger()


def _rpmvercmp(value1, value2):
    '''
    return 1 if value1 newer than value2 otherwise -1.
    in case value1 == value2 return 0.
    '''
    NEWER = 1
    OLDER = -1
    EQUAL = 0

    R_NONALNUM = r'^([^a-zA-Z0-9]*)(.*)$'
    R_DIGITS = r'^([0-9]+)(.*)$'
    R_LETTERS = r'^([a-zA-Z]+)(.*)$'
    
    while value1 or value2:
        match1 = re.match(R_NONALNUM, value1)
        match2 = re.match(R_NONALNUM, value2)

        value1 = match1.group(2)
        value2 = match2.group(2)

        if (match1 := re.match(R_DIGITS, value1)):
            if not (match2 := re.match(R_DIGITS, value2)):
                return NEWER

            if int(match1.group(1)) > int(match2.group(1)):
                return NEWER
            elif int(match1.group(1)) < int(match2.group(1)):
                return OLDER

        elif (match2 := re.match(R_DIGITS, value2)):
            return OLDER
        
        else:
            match1 = re.match(R_LETTERS, value1)
            match2 = re.match(R_LETTERS, value2)

            if not match2 and match1:
                return NEWER
            elif match2 and not match1:
                return OLDER
            elif not match2 and not match1:
                return EQUAL

            if match1.group(1) > match2.group(1):
                return NEWER
            elif match1.group(1) < match2.group(1):
                return OLDER

        value1 = match1.group(2)
        value2 = match2.group(2)

    if len(value1) == len(value2) == 0:
        return EQUAL
    if len(value1) != 0:
        return NEWER
    return OLDER


def check_version(pack1, pack2):
    '''
    return True if pack1 newer than pack2
    '''
    if pack1['epoch'] != pack2['epoch']:
        return pack1['epoch'] > pack2['epoch']

    if ((result := _rpmvercmp(pack1['version'], pack2['version'])) != 0):
        return result == 1

    if ((result := _rpmvercmp(pack1['release'], pack2['release'])) != 0):
        return result == 1

    return False


async def _query(branch, arch, timeout):
    session_timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=session_timeout) as session:

        async with session.get(URL.format(branch),
                               params={'arch': arch}) as resp:

            return (branch, resp.status, json.loads(await resp.text()))


async def query_bins(arch, timeout):
    queries = [asyncio.create_task(_query('p10', arch, timeout)),
               asyncio.create_task(_query('sisyphus', arch, timeout))]

    responses = await asyncio.gather(*queries, return_exceptions=True)

    if any(map(lambda value: isinstance(value, asyncio.TimeoutError), responses)):
        log.error('Timeout error during request execution. Use --timeout option')
        exit(1)

    if any(map(lambda value: value[1] != 200, responses)):
        log.error('Error when making a request')
        exit(1)

    mappings = {}
    for response in responses:
        mappings[response[0]] = {
            package['name']: package for package in response[2]['packages']
        }

    result = {
        'arch': arch,
        'total_uniq_p10': 0,
        'total_uniq_sisyphus': 0,
        'total_higher_version': 0,
        'uniq_p10': [],
        'uniq_sisyphus': [],
        'higher_version': [],
    }

    for name, package in mappings['p10'].items():
        if not mappings['sisyphus'].get(name, None):
            result['total_uniq_p10'] += 1
            result['uniq_p10'].append(package)

    for name, package in mappings['sisyphus'].items():
        if not mappings['p10'].get(name, None):
            result['total_uniq_sisyphus'] += 1
            result['uniq_sisyphus'].append(package)

        elif check_version(package, mappings['p10'][name]):
            result['total_higher_version'] += 1
            result['higher_version'].append(package)

    with suppress(BrokenPipeError):
        print(json.dumps(result))


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
