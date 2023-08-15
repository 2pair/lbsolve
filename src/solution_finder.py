from copy import deepcopy
from sortedcontainers import SortedDict
from threading import Lock, Thread

from lbsolve.game_dictionary import GameDictionary, Word


# best solution should be fewest words, then fewest letters
class SolutionNode:
    def __init__(self, word: Word, parent_node=None):
        self.word = word
        self.next_nodes = SortedDict()  # {num_unique: [candidates]}}
        self.prev_node = parent_node
        self.uniques_in_sequence = set()

    def __iter__(self):
        return self

    def __next__(self):
        for next_node in self.next_nodes:
            yield next_node
        raise StopIteration

    def add_child(self, word):
        new_node = SolutionNode(word, self)
        new_node.uniques_in_sequence = self.uniques_in_sequence + set(word)
        next_nodes_list = self.next_nodes.setDefault(new_node.uniques_in_Sequence, [])
        next_nodes_list.append(new_node)
        return new_node


class SolutionCandidate:
    def __init__(self):
        self.sequence = []
        self.last_letter = None
        self.unique_letters = set()

    def length(self):
        return len(self.sequence)

    def add_word(self, word: Word):
        if self.last_letter and self.last_letter != word.first_letter:
            raise ValueError(
                "First letter of new word does not match last letter of last word"
            )
        self.sequence.append(word)
        self.unique_letters.update(word.unique_letters)
        self.last_letter = word.last_letter


class SolutionFinder:
    def __init__(self, game_dictionary: GameDictionary):
        self.game_dictionary = game_dictionary
        self._solution_candidates = {}  # {last_letter: {num_unique: [candidates]}}
        self.solutions = {}  # {num_words_in_solution: [solutions]}
        self._solutions_lock = Lock()
        self._thread_should_stop = False
        self._solver_thread = Thread(target=self.find_solutions)

    @staticmethod
    def _add_to_solutions_list(solutions_list, candidate):
        letter_group = solutions_list.get(candidate.last_letter, {})
        uniques_group = letter_group.get(len(candidate.unique_letters), [])
        uniques_group.append(candidate)

    def _seed_candidates(self):
        print("seeding candidates")
        total = 0
        for word in self.game_dictionary.ordered_by_uniques():
            # print(f"word is {word}")
            candidate = SolutionCandidate()
            candidate.add_word(word)
            self._add_to_solutions_list(self._solution_candidates, candidate)
            total += 1
            print(f"Added new candidate. running total is {total}")

    def step(self):
        """add one level to the solutions"""
        if not self._solution_candidates:
            self._seed_candidates()
            return
        new_solutions = {}
        for word in self.game_dictionary.ordered_by_uniques():
            partial_solutions = self._solution_candidates[word.last_letter]
            for partial_solution in partial_solutions:
                new_candidate = deepcopy(partial_solution)
                new_candidate.add_word(word)
                self._add_to_solutions_list(new_solutions, new_candidate)
                if new_candidate.unique_letters == 12:
                    solutions = self.solutions.get(new_candidate.length(), [])
                    solutions.append(new_candidate)
                    print(f"found solution {new_candidate.sequence.join(', ')}")
        self._solution_candidates.update(new_solutions)

    def start(self):
        pass

    def stop(self):
        pass
