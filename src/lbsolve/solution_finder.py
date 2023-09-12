"""Class to find new solutions and data structures to aid in representation."""
from __future__ import annotations
from collections import OrderedDict
from collections.abc import Mapping
from copy import deepcopy
from threading import Lock, Thread
import time
from typing import Generator, Iterable

from lbsolve.game_dictionary import GameDictionary, Word, WordSequence
from lbsolve.type_defs import Letter, UniqueCount, WordCount


class PartialSolution:
    """
    Represents a series of words that do not use all game letters.

    This class is write-once
    """

    sequence: WordSequence
    last_letter: str
    unique_letters: frozenset

    def __init__(self, sequence: WordSequence) -> None:
        """
        Args:
          sequence: The sequence of words in the partial solution.
        """
        self.sequence = sequence
        self.last_letter = sequence[-1].last_letter
        self.unique_letters = frozenset(
            letter for word in sequence for letter in word.unique_letters
        )

    def __len__(self) -> int:
        return len(self.sequence)

    def clone_and_extend(self, word: Word) -> WordSequence:
        """Creates a new word sequence equal to self + word.

        Args:
          word: The new word to add to the sequence

        Returns: The new sequence of words."""
        if self.last_letter and self.last_letter != word.first_letter:
            raise ValueError(
                "First letter of new word does not match last letter of last word"
            )
        return PartialSolution(WordSequence(*self.sequence, word))

    def __eq__(self, other: PartialSolution) -> bool:
        return self.sequence == other.sequence

    def __str__(self) -> str:
        words = []
        for word in self.sequence:
            word_str = str(word)
            words.append(word_str)
        words = [str(word) for word in self.sequence]
        joined = "-".join(words)
        return joined


class PartialSolutionMap(Mapping):
    """
    Data structure that provides various access methods to partial solutions.
    """

    candidates_by_uniques_by_last_letter: dict[
        Letter, dict[UniqueCount, list[PartialSolution]]
    ]
    candidates_by_last_letter_by_uniques: dict[
        UniqueCount, dict[Letter, list[PartialSolution]]
    ]
    linear_candidates: list[PartialSolution]
    count: int

    def __init__(self) -> None:
        super().__init__()
        self.candidates_by_uniques_by_last_letter = {}
        self.candidates_by_last_letter_by_uniques = {}
        self.linear_candidates = []
        self.count = 0

    def insert(self, candidate: PartialSolution) -> None:
        """
        Add a new partial solution to the data structure.

        Args:
          candidate: The partial solution to add.
        """
        solutions_by_uniques = self.candidates_by_uniques_by_last_letter.setdefault(
            candidate.last_letter, {}
        )
        solutions_list = solutions_by_uniques.setdefault(
            len(candidate.unique_letters), []
        )
        solutions_list.append(candidate)

        solutions_by_last_letter = self.candidates_by_last_letter_by_uniques.setdefault(
            len(candidate.unique_letters), {}
        )
        solutions_list = solutions_by_last_letter.setdefault(candidate.last_letter, [])
        solutions_list.append(candidate)

        self.linear_candidates.append(candidate)
        self.count += 1

    def merge(self, other: Iterable[PartialSolution]) -> None:
        """
        Merge a sequence of partial solutions into this instance.
        """
        for candidate in other:
            if candidate in self.linear_candidates:
                continue
            self.insert(candidate)

    def __getitem__(
        self,
        lookup: Letter
        or UniqueCount
        or tuple[Letter, UniqueCount]
        or tuple[UniqueCount, Letter],
    ) -> dict[list[PartialSolution]] or list[PartialSolution]:
        if isinstance(lookup, Letter):
            candidates_by_uniques = self.candidates_by_uniques_by_last_letter.get(
                lookup, {}
            )
            return [
                candidate
                for candidates in candidates_by_uniques.values()
                for candidate in candidates
            ]
        if isinstance(lookup, UniqueCount):
            candidates_by_last_letter = self.candidates_by_last_letter_by_uniques.get(
                lookup, {}
            )
            return [
                candidate
                for candidates in candidates_by_last_letter.values()
                for candidate in candidates
            ]
        if isinstance(lookup, tuple):
            if isinstance(lookup[0], Letter) and isinstance(lookup[1], UniqueCount):
                return self.candidates_by_uniques_by_last_letter.get(lookup[0], {}).get(
                    lookup[1], []
                )
            if isinstance(lookup[0], UniqueCount) and isinstance(lookup[1], Letter):
                return self.candidates_by_last_letter_by_uniques.get(lookup[0], {}).get(
                    lookup[1], []
                )
        raise LookupError("Provided key type is not valid.")

    def __iter__(self) -> Generator[PartialSolution]:
        for candidate in self.linear_candidates:
            yield candidate

    def __len__(self) -> int:
        return self.count


Solution = PartialSolution


class SolutionList(Mapping):
    """
    Data structure to represent solutions.
    """

    solutions_by_words: OrderedDict[UniqueCount, list[PartialSolution]]
    linear_solutions = list[PartialSolution]
    count: int

    def __init__(self) -> None:
        super().__init__()
        self.solutions_by_words = OrderedDict()
        self.linear_solutions = []
        self.count = 0

    def insert(self, solution: Solution) -> None:
        """
        Add a solution to the data structure.

        Args:
          solution: A puzzle solution.
        """
        solutions_list = self.solutions_by_words.setdefault(len(solution), [])
        if not solutions_list:
            # maintain ascending key order
            ascending_keys = sorted(self.solutions_by_words.keys())
            for key in ascending_keys:
                self.solutions_by_words.move_to_end(key)

        solutions_list.append(solution)
        self.linear_solutions.append(solution)
        self.count += 1

    def flatten(self) -> list[Solution]:
        """A one dimensional representation of the data.

        Returns: list of solutions.
        """
        return self.linear_solutions

    def __getitem__(
        self, lookup: WordCount or tuple[WordCount, UniqueCount]
    ) -> Solution:
        if isinstance(lookup, WordCount):
            return self.solutions_by_words[lookup]
        if isinstance(lookup, tuple):
            return self.solutions_by_words[lookup[0]][lookup[1]]
        raise LookupError("Provided key type is not valid.")

    def __contains__(self, item: object) -> bool:
        return item in self.linear_solutions

    def __iter__(self) -> Generator[Solution]:
        for solution_list in self.solutions_by_words.values():
            for solution in solution_list:
                yield solution

    def __len__(self) -> int:
        return self.count

    def __eq__(self, other: object) -> bool:
        return self.linear_solutions == other.linear_solutions


class SolutionFinder:
    """
    Runs solution search algorithms in a thread.
    """

    game_dictionary: GameDictionary
    max_depth: int
    solutions: SolutionList
    _solutions_lock: Lock
    _solver_thread: Thread
    _thread_should_stop: bool
    # Only accessed in thread
    _solution_candidates: PartialSolutionMap

    def __init__(self, game_dictionary: GameDictionary, max_depth: int = None) -> None:
        """
        Args:
          game_dictionary: The dictionary of game words.
          max_depth: The maximum number of words to consider within a word sequence.
        """
        self.game_dictionary = game_dictionary
        self.max_depth = max_depth
        self.solutions = SolutionList()
        self._solutions_lock = Lock()
        self._solver_thread = Thread(
            target=self._find_solutions_depth_first, daemon=True
        )
        self._thread_should_stop = False
        self._solution_candidates = PartialSolutionMap()

    def _seed_candidates(self) -> PartialSolutionMap:
        """
        Pre-populates single-word partial solutions.

        Returns: A PartialSolutionMap with single-word partial solutions.
        """
        print("seeding candidates")
        new_candidates = PartialSolutionMap()
        for word in self.game_dictionary.ordered_by_first_letter():
            candidate = PartialSolution(WordSequence(word))
            new_candidates.insert(candidate)
        return new_candidates

    def start(self) -> None:
        """Starts the solver thread."""
        self._solver_thread.start()

    def stop(self, join: bool = False) -> None:
        """
        Stops the solver thread.

        join: If true, waits for the thread to join.
        """
        self._thread_should_stop = True
        if join:
            self._solver_thread.join(10)

    def running(self) -> bool:
        """
        Get the current solver thread status.

        Returns: If the solver thread is running.
        """
        return self._solver_thread.is_alive()

    def solutions_count(self) -> int:
        """
        Get the current count of solutions that have been found.

        Returns: Count of solutions.
        """
        return len(self.solutions)

    def get_solutions(self) -> SolutionList:
        """
        Get all of the current solutions.

        Returns: All known solutions.
        """
        with self._solutions_lock:
            ret_val = deepcopy(self.solutions)
        return ret_val

    def _add_new_solution(self, new_solution: Solution) -> None:
        """
        Add a new solution.

        Args:
          new_solution: A new solution
        """
        with self._solutions_lock:
            self.solutions.insert(new_solution)
        print(
            f"Found new solution: "
            f"{' - '.join([str(word) for word in new_solution.sequence])}"
        )

    @staticmethod
    def _add_word_to_solution_candidates(
        solution_candidates: PartialSolutionMap,
        new_word: Word,
    ) -> PartialSolutionMap:
        """
        Adds a given word to appropriate partial solutions.

        Args:
          solution_candidates: A group of partial solutions.
          new_word: The word to add to the solution candidates.

        Returns: The partial solutions that include the new word.
        """
        new_solution_candidates = PartialSolutionMap()
        candidates = solution_candidates[new_word.first_letter]
        for solution_candidate in candidates:
            if new_word in solution_candidate.sequence:
                continue
            new_candidate = solution_candidate.clone_and_extend(new_word)
            new_solution_candidates.insert(new_candidate)
        return new_solution_candidates

    def _promote_candidates(self, candidates: PartialSolutionMap) -> list[Solution]:
        """
        Validate if any partial solution meets the criteria to become a solution.

        Args:
          candidates: The partial solutions to check.

        Returns: Newly found solutions.
        """
        new_solutions = []
        num_game_letters = len(self.game_dictionary.get_letter_candidates())
        for new_candidate in candidates:
            if len(new_candidate.unique_letters) != num_game_letters:
                continue
            if new_candidate in self.solutions:
                continue
            new_solutions.append(new_candidate)
            self._add_new_solution(new_solutions[-1])
        return new_solutions

    def _mutate_solution_candidates(self) -> int:
        """
        Iterates current candidates in a breadth first manner. by testing each
        candidate against all words in the game dictionary.

        Returns: Count of newly found solutions.
        """
        new_candidates = PartialSolutionMap()
        start_time = time.time()
        for i, word in enumerate(self.game_dictionary.ordered_by_first_letter()):
            child_candidates = self._add_word_to_solution_candidates(
                self._solution_candidates, word
            )
            new_candidates.merge(child_candidates)
            if i % 20 == 0:
                print(f"mutated 20 words in {time.time() - start_time} s")
                start_time = time.time()
        new_solutions = self._promote_candidates(new_candidates)
        partial_solutions = filter(
            lambda candidate: candidate not in new_solutions, new_candidates
        )
        self._solution_candidates.merge(partial_solutions)
        return len(new_solutions)

    def _find_solutions_breadth_first(self) -> None:
        """
        Iterate through all words, finding all other words that can follow
        after it and identifying any sequences that meet solution criteria.
        """
        self._solution_candidates = self._seed_candidates()
        have_solutions = False
        depth = 0
        while not self._thread_should_stop:
            depth += 1
            new_solutions_count = self._mutate_solution_candidates()
            if new_solutions_count:
                have_solutions = True
            if have_solutions and new_solutions_count == 0:
                # If adding more words didn't help we can stop looking
                print("stopping search because no more solutions were found.")
                break
            if self.max_depth and depth >= self.max_depth:
                print("stopping search because max depth has been reached.")
                break
        print("Search has ended.")

    def _find_solutions_depth_first(self) -> None:
        """
        Iterate through the most promising words in the game dictionary,
        looking first at the other most promising words for potential sequences of
        words.
        """
        self._solution_candidates = PartialSolutionMap()
        num_game_letters = len(self.game_dictionary.get_letter_candidates())
        one_word_solutions = PartialSolutionMap()
        for word in self.game_dictionary.get_words_with_uniques(num_game_letters):
            one_word_solutions.insert(PartialSolution(WordSequence(word)))
            self._promote_candidates(one_word_solutions)

        for loop in range(0, num_game_letters):
            print(f"running meta pass {loop}")
            for number in reversed(range(1, num_game_letters)):
                print(f"processing words with {number} unique letters")
                for word in self.game_dictionary.get_words_with_uniques(number):
                    candidate = PartialSolution(WordSequence(word))
                    self._solution_candidates.insert(candidate)
                print(
                    f"Generated {len(self._solution_candidates)} "
                    "candidates with root words."
                )
                last_candidates_len = len(self._solution_candidates)
                last_solutions_count = self.solutions_count()
                for word in self.game_dictionary.get_words_with_uniques(number):
                    child_candidates = self._add_word_to_solution_candidates(
                        self._solution_candidates, word
                    )
                    new_solutions = self._promote_candidates(child_candidates)
                    partial_solutions = filter(
                        lambda candidate: candidate not in new_solutions,
                        child_candidates,
                    )
                    self._solution_candidates.merge(partial_solutions)
                print(
                    f"Created {len(self._solution_candidates) - last_candidates_len} "
                    "two word candidates"
                )
                print(
                    f"Found {self.solutions_count() - last_solutions_count} new "
                    "solutions"
                )
