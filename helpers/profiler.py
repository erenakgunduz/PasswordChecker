import asyncio
import cProfile
import pstats
from os import getcwd

import passwordtool


def main():
    with cProfile.Profile() as pr:
        asyncio.run(passwordtool.collect_lists())
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()
    stats.dump_stats(filename=f"{getcwd()}/profile.prof")


if __name__ == "__main__":
    main()
