import asyncio
import argparse

import aiohttp

from .const import ARCHITECTURES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "arch",
        choices=ARCHITECTURES,
        help="arch is desired architecture.",
    )
    args = parser.parse_args()


if __name__ == '__main__':
    main()
