from os import getcwd
import cProfile
import pstats
import passwordtool


def main():
    with cProfile.Profile() as pr:
        passwordtool.main()
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()
    stats.dump_stats(filename=f"{getcwd()}/profile-m.prof")


if __name__ == "__main__":
    main()
