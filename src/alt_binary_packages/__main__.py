import asyncio
import argparse
import logging
import json
import re
from contextlib import suppress

import aiohttp

from .const import ARCHITECTURES, BRANCHES, URL, TIMEOUT

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


async def query_bins(main_branch, aux_branch, arch, timeout):
    queries = [
        asyncio.create_task(_query(main_branch, arch, timeout)),
        asyncio.create_task(_query(aux_branch, arch, timeout))
    ]

    responses = await asyncio.gather(*queries, return_exceptions=True)

    if any(map(lambda value: isinstance(value, asyncio.TimeoutError), responses)):
        log.error('Timeout error during request execution. Use --timeout option')
        return None

    if any(map(lambda value: value[1] != 200, responses)):
        log.error('Error when making a request')
        return None

    mappings = {}
    for response in responses:
        mappings[response[0]] = {
            package['name']: package for package in response[2]['packages']
        }

    result = {
        'arch': arch,
        f'total_uniq_{aux_branch}': 0,
        f'total_uniq_{main_branch}': 0,
        'total_higher_version': 0,
        f'uniq_{aux_branch}': [],
        f'uniq_{main_branch}': [],
        'higher_version': [],
    }

    for name, package in mappings[aux_branch].items():
        if not mappings[main_branch].get(name, None):
            result[f'total_uniq_{aux_branch}'] += 1
            result[f'uniq_{aux_branch}'].append(package)

    for name, package in mappings[main_branch].items():
        if not mappings[aux_branch].get(name, None):
            result[f'total_uniq_{main_branch}'] += 1
            result[f'uniq_{main_branch}'].append(package)

        elif check_version(package, mappings[aux_branch][name]):
            result['total_higher_version'] += 1
            result['higher_version'].append(package)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'main_branch',
        choices=BRANCHES,
        help=(
            'the main branch against which new versions of packages '
            'will be checked'
        ),
    )
    parser.add_argument(
        'aux_branch',
        choices=BRANCHES,
        help='auxiliary branch for version comparison',
    )
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

    result = asyncio.run(
        query_bins(args.main_branch, args.aux_branch, args.arch, args.timeout)
    )

    if not result:
        exit(1)

    with suppress(BrokenPipeError):
        print(json.dumps(result))


if __name__ == '__main__':
    main()
