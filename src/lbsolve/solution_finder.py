from __future__ import annotations
from collections import OrderedDict
from collections.abc import Mapping
from copy import deepcopy
from threading import Lock, Thread
from typing import Generator

from lbsolve.game_dictionary import GameDictionary, Word, WordSequence


class SolutionCandidate:
    """This class is write-once"""

    sequence: WordSequence
    last_letter: str
    unique_letters: frozenset

    def __init__(self, sequence: WordSequence) -> None:
        self.sequence = sequence
        self.last_letter = sequence[-1].last_letter
        self.unique_letters = frozenset(
            letter for word in sequence for letter in word.unique_letters
        )

    def __len__(self) -> int:
        return len(self.sequence)

    def clone_and_extend(self, word: Word) -> WordSequence:
        if self.last_letter and self.last_letter != word.first_letter:
            raise ValueError(
                "First letter of new word does not match last letter of last word"
            )
        return SolutionCandidate(WordSequence(*self.sequence, word))

    def __eq__(self, other: SolutionCandidate) -> bool:
        return self.sequence == other.sequence


class CandidateMap(Mapping):
    candidates_by_uniques_by_last_letter: dict[str, dict[int, list[SolutionCandidate]]]
    candidates_by_last_letter_by_uniques: dict[int, dict[str, list[SolutionCandidate]]]
    linear_candidates: list[SolutionCandidate]
    count: int

    def __init__(self) -> None:
        super().__init__()
        self.count = 0
        self.candidates_by_uniques_by_last_letter = {}
        self.candidates_by_last_letter_by_uniques = {}
        self.linear_candidates = []

    def insert(self, candidate: SolutionCandidate) -> None:
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

    def merge(self, other: CandidateMap) -> None:
        for candidate in other:
            self.insert(candidate)

    def __getitem__(
        self, lookup: str | int | tuple[str, int]
    ) -> dict[list[SolutionCandidate]] | list[SolutionCandidate]:
        if isinstance(lookup, str):
            return self.candidates_by_uniques_by_last_letter.get(lookup, {})
        if isinstance(lookup, int):
            return self.candidates_by_last_letter_by_uniques.get(lookup, {})
        if isinstance(lookup, tuple):
            if isinstance(lookup[0], str) and isinstance(lookup[1], int):
                return self.candidates_by_uniques_by_last_letter.get(lookup[0], {}).get(
                    lookup[1], []
                )
            if isinstance(lookup[0], int) and isinstance(lookup[1], str):
                return self.candidates_by_last_letter_by_uniques.get(lookup[0], {}).get(
                    lookup[1], []
                )
        raise LookupError("Provided key type is not valid.")

    def __iter__(self) -> Generator[SolutionCandidate]:
        for candidate in self.linear_candidates:
            yield candidate

    def __len__(self) -> int:
        return self.count


class SolutionList(Mapping):
    solutions_by_words: OrderedDict[int, list[SolutionCandidate]]
    count: int

    def __init__(self) -> None:
        super().__init__()
        self.solutions_by_words = OrderedDict()
        self.count = 0

    def insert(self, solution: SolutionCandidate) -> None:
        solutions_list = self.solutions_by_words.setdefault(len(solution), [])
        if not solutions_list:
            # maintain ascending key order
            ascending_keys = sorted(self.solutions_by_words.keys())
            for key in ascending_keys:
                self.solutions_by_words.move_to_end(key)

        solutions_list.append(solution)
        self.count += 1

    def flatten(self) -> list[SolutionCandidate]:
        return [
            solution
            for solution_group in self.solutions_by_words.values()
            for solution in solution_group
        ]

    def __getitem__(self, lookup: int | tuple[int, int]) -> SolutionCandidate:
        if isinstance(lookup, int):
            return self.solutions_by_words[lookup]
        if isinstance(lookup, tuple):
            return self.solutions_by_words[lookup[0]][lookup[1]]
        raise LookupError("Provided key type is not valid.")

    def __iter__(self) -> Generator[SolutionCandidate]:
        for solution_list in self.solutions_by_words.values():
            for solution in solution_list:
                yield solution

    def __len__(self) -> int:
        return self.count


class SolutionFinder:
    game_dictionary: GameDictionary
    max_depth: int
    solutions: SolutionList
    _solutions_lock: Lock
    _solver_thread: Thread
    _thread_should_stop: bool
    # Only accessed in thread
    _solution_candidates: CandidateMap

    def __init__(self, game_dictionary: GameDictionary, max_depth: int = None) -> None:
        self.game_dictionary = game_dictionary
        self.max_depth = max_depth
        self.solutions = SolutionList()
        self._solutions_lock = Lock()
        self._solver_thread = Thread(target=self._find_solutions, daemon=True)
        self._thread_should_stop = False
        self._solution_candidates = CandidateMap()

    def _seed_candidates(self) -> CandidateMap:
        print("seeding candidates")
        new_candidates = CandidateMap()
        for word in self.game_dictionary.ordered_by_uniques():
            candidate = SolutionCandidate(WordSequence(word))
            new_candidates.insert(candidate)
        return new_candidates

    def start(self) -> None:
        self._solver_thread.start()

    def stop(self, join: bool = False) -> None:
        self._thread_should_stop = True
        if join:
            self._solver_thread.join(10)

    def running(self) -> bool:
        return self._solver_thread.is_alive()

    def get_solutions(self) -> SolutionList:
        with self._solutions_lock:
            ret_val = deepcopy(self.solutions)
        return ret_val

    def _add_new_solution(self, new_solution: SolutionCandidate) -> None:
        with self._solutions_lock:
            self.solutions.insert(new_solution)
        print(
            f"Found new solution: "
            f"{' - '.join([str(word) for word in new_solution.sequence])}"
        )

    @staticmethod
    def _add_word_to_solution_candidates(
        solution_candidates: CandidateMap, new_word: Word
    ) -> CandidateMap:
        new_solution_candidates = CandidateMap()
        for solution_candidate in solution_candidates:
            new_candidate = solution_candidate.clone_and_extend(new_word)
            new_solution_candidates.insert(new_candidate)
        return new_solution_candidates

    def _mutate_solution_candidates(self) -> int:
        found_solutions = 0
        num_game_letters = self.game_dictionary.get_letter_candidates()
        new_candidates = CandidateMap()
        words_by_letter = self.game_dictionary.ordered_by_first_letter()
        for word in words_by_letter:
            partial_solution_group = self._solution_candidates[word.first_letter]
            child_candidates = self._add_word_to_solution_candidates(
                partial_solution_group, word
            )
            new_candidates.merge(child_candidates)
        self._solution_candidates.merge(new_candidates)

        for new_candidate in new_candidates:
            if len(new_candidate.unique_letters) != num_game_letters:
                continue
            new_solution = new_candidate
            self._add_new_solution(new_solution)
            found_solutions += 1
        return found_solutions

    def _find_solutions(self) -> None:
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
                break
            if self.max_depth and depth >= self.max_depth:
                break
