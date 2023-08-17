from __future__ import annotations
from collections.abc import Mapping
from copy import deepcopy
from threading import Event, Lock, Thread

from lbsolve.game_dictionary import GameDictionary, Word, WordSequence


class SolutionCandidate:
    """This class is write-once"""

    sequence: WordSequence
    last_letter: str
    unique_letters: set

    def __init__(self, sequence: WordSequence):
        self.sequence = sequence
        self.last_letter = sequence[-1].last_letter
        self.unique_letters = {
            letter for word in sequence for letter in word.unique_letters
        }

    def __len__(self):
        return len(self.sequence)

    def clone_and_extend(self, word: Word):
        if self.last_letter and self.last_letter != word.first_letter:
            raise ValueError(
                "First letter of new word does not match last letter of last word"
            )
        return SolutionCandidate(WordSequence(*self.sequence, word))


class CandidateMap(Mapping):
    candidates_by_uniques_by_last_letter: dict[str, dict[int, list[SolutionCandidate]]]
    candidates_by_last_letter_by_uniques: dict[int, dict[str, list[SolutionCandidate]]]
    count: int = 0

    def insert(self, solution: SolutionCandidate):
        solutions_by_uniques = self.candidates_by_uniques_by_last_letter.get(
            solution.last_letter, {}
        )
        solutions_list = solutions_by_uniques.get(len(solution.unique_letters, []))
        solutions_list.append(solution)

        solutions_by_last_letter = self.candidates_by_last_letter_by_uniques.get(
            solution.unique_letters, {}
        )
        solutions_list = solutions_by_last_letter.get(len(solution.last_letter, []))
        solutions_list.append(solution)
        count += 1

    def merge(self, other: CandidateMap):
        pass  # TODO

    def __getitem__(
        self, lookup: str | int | tuple[str, int]
    ) -> dict[list[SolutionCandidate]] | list[SolutionCandidate]:
        if isinstance(lookup, str):
            return self.candidates_by_last_letter_by_uniques[lookup]
        if isinstance(lookup, int):
            return self.candidates_by_uniques_by_last_letter[lookup]
        if isinstance(lookup, tuple):
            return self.candidates_by_last_letter_by_uniques[lookup[0]][lookup[1]]
        raise LookupError("Provided key type is not valid.")

    def __iter__(self):
        return self

    def __len__(self):
        return self.count


class SolutionList(Mapping):
    solutions_by_words: dict[int, list[SolutionCandidate]]
    count: int = 0

    def insert(self, solution: SolutionCandidate):
        solutions_list = self.solutions_by_words.get(len(solution), [])
        solutions_list.append(solution)
        count += 1

    def __getitem__(self, lookup: int | tuple[int, int]):
        if isinstance(lookup, int):
            return self.solutions_by_words[lookup]
        if isinstance(lookup, tuple):
            return self.solutions_by_words[lookup[0]][lookup[1]]
        raise LookupError("Provided key type is not valid.")

    def __iter__(self):
        return self

    def __len__(self):
        return self.count


class SolutionFinder:
    game_dictionary: GameDictionary
    solutions: SolutionList
    _solutions_lock: Lock
    _new_solutions_event: Event
    _solver_thread: Thread
    _thread_should_stop: bool
    # Only access in thread
    _solution_candidates: CandidateMap

    def __init__(self, game_dictionary: GameDictionary):
        self.game_dictionary = game_dictionary
        self.solutions = SolutionList()
        self._solutions_lock = Lock()
        self._new_solutions_event = Event()
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

    def start(self):
        self._solver_thread.start()

    def stop(self, join: bool = False):
        self._thread_should_stop = True
        if join:
            self._solver_thread.join(10)

    def get_solutions(self) -> SolutionList:
        self._new_solutions_event.wait()
        with self._solutions_lock:
            ret_val = deepcopy(self.solutions)
        self._new_solutions_event.clear()
        return ret_val

    def get_solutions_flat(self) -> list:
        solutions = self.get_solutions()
        return [
            solution
            for solution_group in solutions.values()
            for solution in solution_group
        ]

    def _add_new_solution(self, new_solution: SolutionCandidate):
        with self._solutions_lock:
            self.solutions.insert(new_solution)
        print(
            f"Found new solution: {' - '.join([str(word) for word in new_solution.sequence])}"
        )
        self._new_solutions_event.set()

    def _add_word_to_solution_candidates(
        self, solution_candidates: CandidateMap, new_word: Word
    ) -> CandidateMap:
        new_solution_candidates = CandidateMap()
        for solution_candidate in solution_candidates:
            candidate = solution_candidate.insert(new_word)
            new_solution_candidates.insert(candidate)
        return new_solution_candidates

    def _add_to_solution_candidates(self) -> int:
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
            if len(new_candidate.unique_letters) == num_game_letters:
                new_solution = new_candidate
                self._add_new_solution(new_solution)
                found_solutions += 1
        return found_solutions

    def _find_solutions(self):
        self._solution_candidates = self._seed_candidates()
        have_solutions = False
        while not self._thread_should_stop:
            found = self._add_to_solution_candidates()
            if found:
                have_solutions = True
            if have_solutions and found == 0:
                # If adding more words didn't help we can stop looking
                break