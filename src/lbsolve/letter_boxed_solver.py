from argparse import ArgumentParser
from pathlib import Path
import time

from lbsolve.game_dictionary import GameDictionary
from lbsolve.solution_finder import SolutionFinder


def split_letter_group(group):
    """turn a string into a list!"""
    return list(group.strip())


def main():
    arg_parser = ArgumentParser(description="Solves NYT Letter Boxed puzzles")
    arg_parser.add_argument(
        "--letter_groups",
        type=split_letter_group,
        nargs=4,
        required=True,
        help="The four letter groups, given as 'abc def ghi jkl'",
    )
    arg_parser.add_argument(
        "--word_file",
        type=Path,
        default="/usr/share/dict/words",
        required=False,
        help="Path to a dictionary file. One word per line.",
    )
    arg_parser.add_argument(
        "--max_depth",
        type=int,
        default=0,
        required=False,
        help="Max consecutive words in a solution. 0 for any.",
    )

    args = arg_parser.parse_args()

    start = time.time()
    print("creating game dictionary from file...", end="")
    game_dictionary = GameDictionary(args.word_file, args.letter_groups)
    game_dictionary.create()
    # TODO: Add blacklist
    print(f"done in {time.time() - start:.3f} seconds")
    print(
        f"from {game_dictionary.valid_words + game_dictionary.invalid_words} input words found {game_dictionary.valid_words} valid words"
    )

    print("Searching for solutions...", end="")
    solver = SolutionFinder(game_dictionary, args.max_depth)
    solver.start()
    while solver.running():
        try:
            solutions = solver.get_solutions()
            if solutions:
                print(
                    f"found {len(solutions)} solutions. current best solution is {' - '.join(solutions[0])}",
                    end="\r",
                    flush=True,
                )
        except KeyboardInterrupt:
            print("User requests stop.")
            break
        finally:
            solver.stop()
    solutions = solver.get_solutions()
    for solution in solutions:
        print(solution)
