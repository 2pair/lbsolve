"""Takes CLI arguments and runs the solution finder.x"""
from argparse import ArgumentParser
from pathlib import Path
import time

from lbsolve.game_dictionary import GameDictionary
from lbsolve.solution_finder import SolutionFinder


def split_letter_group(group):
    """turn a string into a list!"""
    return list(group.strip())


def main():
    """Main function to run when executed as a module."""
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
        f"from {game_dictionary.valid_words + game_dictionary.invalid_words} "
        f"input words found {game_dictionary.valid_words} valid words"
    )

    print("Searching for solutions...", end="")
    solver = SolutionFinder(game_dictionary, args.max_depth)
    solver.start()
    while solver.running():
        try:
            solutions_count = solver.solutions_count()
            if solutions_count:
                solutions = solver.get_solutions()
                print(
                    f"found {len(solutions)} solutions. current best solution "
                    f"is {str(solutions.linear_solutions[0])}"
                )  # ,
                #  end="\r",
                #   flush=True,
                # )
            else:
                print(
                    f"found {len(solver._solution_candidates.linear_candidates)} "
                    "candidates."
                )  # ,
                # end="\r",
                # flush=True,
                # )
            time.sleep(0.25)
        except KeyboardInterrupt:
            print("User requests stop.")
            break
    solver.stop()
    solutions = solver.get_solutions()
    for solution in solutions:
        print(solution)
    if not solutions:
        print("No solutions found!")
        unique_counts = (
            solver._solution_candidates.candidates_by_last_letter_by_uniques.keys()
        )
        max_letters = max(unique_counts) if unique_counts else 0
        if not max_letters:
            return
        print(f"closest attempt: {solver._solution_candidates[max_letters][0]}")
