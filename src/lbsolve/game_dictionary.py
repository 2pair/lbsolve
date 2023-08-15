from collections.abc import Sequence
from pathlib import Path


MIN_LETTERS_IN_WORD = 3


class Word:
    _word: str
    first_letter: str
    last_letter: str
    unique_letters: set[str]

    def __init__(self, word: str):
        self._word = word
        self.first_letter = self._word[0]
        self.last_letter = self._word[-1]
        self.unique_letters = set(word)

    def __str__(self):
        return self._word

    def __repr__(self):
        return f"Word({self._word})"


class WordSequence(Sequence):
    _word_sequence: tuple[Word]

    def __init__(self, *words: Word):
        self._word_sequence = (words)

    def __len__(self):
        return len(self._word_sequence)

    def __getitem__(self, index):
        return self._word_sequence[index]

    def __iter__(self):
        return self

    def __next__(self):
        for word in self._word_sequence:
            yield word


class GameDictionary:
    word_list_file: Path
    letter_groups: tuple[tuple[str, 3], 4]
    valid_words: int
    invalid_words: int
    word_trie: dict
    _words_by_first_letter: dict[str, dict[int, str]]
    _words_by_uniques: dict[int, dict[str, str]]

    def __init__(self, word_list_file: Path, game_letter_groups):
        self.word_list_file = word_list_file
        self.letter_groups = game_letter_groups
        self.valid_words = 0
        self.invalid_words = 0
        self.word_trie = {}
        self._words_by_first_letter = {}
        self._words_by_uniques = {}

    def get_letter_candidates(self, current_letter=""):
        """Letters on sides that don't contain this letter."""
        candidates = list()
        for letter_group in self.letter_groups:
            if current_letter in letter_group:
                continue
            candidates.extend(letter_group)
        return candidates

    def word_is_valid(self, word):
        """Ensure word can be used in game."""
        if len(word) < MIN_LETTERS_IN_WORD:
            return False
        if word[0] not in self.get_letter_candidates():
            return False
        for prev_index, letter in enumerate(word[1:]):
            if letter not in self.get_letter_candidates(word[prev_index]):
                return False
        return True

    @classmethod
    def _add_to_node(cls, parent, letters):
        """Adds the letters onto the given node."""
        current_letter = letters[0] if letters else None
        if current_letter not in parent:
            if current_letter:
                parent[current_letter] = dict()
            else:
                parent[None] = None
                return parent

        if current_letter:
            return cls._add_to_node(parent.get(current_letter), letters[1:])

    def _add_to_trie(self, words_trie, word):
        """Adds a word to the data structure."""
        letters = list(word)
        unique_letters = set(letters)
        # root node
        last_node = self._add_to_node(words_trie, letters)
        # mark word termination
        last_node[None] = {
            "unique_letters": unique_letters,
            "num_uniques": len(unique_letters),
        }

    def create_trie(self):
        """One word per line"""
        self.words_trie = dict()
        with self.word_list_file.open(mode="r") as word_list:
            for word in word_list:
                word = word.strip()
                if not self.word_is_valid(word):
                    self.invalid_words += 1
                    continue
                self._add_to_trie(self.words_trie, word)
                self.valid_words += 1

    def _setup_words_by_uniques(self):
        game_letter_count = 0
        for letter_group in self.letter_groups:
            game_letter_count += len(letter_group)
        for i in range(game_letter_count):
            self._words_by_uniques[i] = {}
            for group in self.letter_groups:
                for letter in group:
                    self._words_by_uniques[i][letter] = []

    def _setup_words_by_first_letter(self):
        game_letter_count = 0
        for letter_group in self.letter_groups:
            game_letter_count += len(letter_group)
        for group in self.letter_groups:
            for letter in group:
                self._words_by_first_letter[letter] = {}
                for i in range(game_letter_count):
                    self._words_by_first_letter[letter][i] = []

    @staticmethod
    def _get_first_letter_group(word: Word, parent: dict, default: dict or list):
        if word.first_letter not in parent.keys():
            parent[word.first_letter] = default
        return parent[word.first_letter]

    @staticmethod
    def _get_unique_letters_group(word: Word, parent: dict, default: dict or list):
        if len(word.unique_letters) not in parent.keys():
            parent[len(word.unique_letters)] = default
        return parent[len(word.unique_letters)]

    def _add_word_to_words_by_first_letter(self, word: Word):
        first_letter_group = self._get_first_letter_group(
            word, self._words_by_first_letter, {}
        )
        uniques_group = self._get_unique_letters_group(word, first_letter_group, [])
        uniques_group.append(word)

    def _add_word_to_words_by_uniques(self, word: Word):
        uniques_group = self._get_unique_letters_group(word, self._words_by_uniques, {})
        first_letter_group = self._get_first_letter_group(word, uniques_group, [])
        first_letter_group.append(word)

    def create_simple(self):
        """One word per line"""
        with self.word_list_file.open(mode="r") as word_list:
            for word_line in word_list:
                raw_word = word_line.strip().lower()
                if not self.word_is_valid(raw_word):
                    self.invalid_words += 1
                    continue
                word = Word(raw_word)
                self._add_word_to_words_by_first_letter(word)
                self._add_word_to_words_by_uniques(word)
                self.valid_words += 1

    def ordered_by_uniques(self):
        words_by_uniques = []
        for first_letters_groups in self._words_by_uniques.values():
            for first_letter_group in first_letters_groups.values():
                for word in first_letter_group:
                    words_by_uniques.append(word)
        return words_by_uniques

    def ordered_by_first_letter(self):
        words_by_first_letter = []
        for uniques_groups in self._words_by_first_letter.values():
            for uniques_group in uniques_groups.values():
                for word in uniques_group:
                    words_by_first_letter.append(word)
        return words_by_first_letter
