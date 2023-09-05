from __future__ import annotations
from collections.abc import Sequence
from pathlib import Path


MIN_LETTERS_IN_WORD = 3


class Word:
    _word: str
    first_letter: str
    last_letter: str
    unique_letters: frozenset[str]

    def __init__(self, word: str) -> None:
        if not isinstance(word, str):
            raise TypeError(
                f"'word' should be type 'str', not '{type(word).__name__}'."
            )
        self._word = word
        self.first_letter = self._word[0]
        self.last_letter = self._word[-1]
        self.unique_letters = frozenset(word)

    def __str__(self) -> str:
        return self._word

    def __repr__(self) -> str:
        return f"Word({self._word})"

    def __eq__(self, other) -> bool:
        return self._word == other._word

    def __hash__(self) -> int:
        return self._word.__hash__()

    @staticmethod
    def factory(*words: str) -> list[Word]:
        return [Word(word) for word in words]


class WordSequence(Sequence):
    _word_sequence: tuple[Word]

    def __init__(self, *words: Word) -> None:
        super().__init__()
        if not words:
            raise IndexError("One or more word expected.")
        if not isinstance(words[0], Word):
            raise TypeError(
                f"'words' should be instances of type 'Word', "
                f"not '{type(words[0]).__name__}'."
            )
        self._word_sequence = words

    def __len__(self) -> int:
        return len(self._word_sequence)

    def __getitem__(self, index) -> Word:
        return self._word_sequence[index]

    def __eq__(self, other: object) -> bool:
        return self._word_sequence == other._word_sequence


class GameDictionary:
    word_list_file: Path
    letter_groups: tuple[tuple[str, 3], 4]
    valid_words: int
    invalid_words: int
    _words_by_first_letter: dict[str, dict[int, str]]
    _words_by_uniques: dict[int, dict[str, str]]

    def __init__(self, word_list_file: Path, game_letter_groups) -> None:
        self.word_list_file = word_list_file
        self.letter_groups = game_letter_groups
        self.valid_words = 0
        self.invalid_words = 0
        self._words_by_first_letter = {}
        self._words_by_uniques = {}

    def get_letter_candidates(self, current_letter="") -> list[tuple[str]]:
        """Letters on sides that don't contain this letter."""
        candidates = []
        for letter_group in self.letter_groups:
            if current_letter in letter_group:
                continue
            candidates.extend(letter_group)
        return candidates

    def word_is_valid(self, word: str) -> bool:
        """Ensure word can be used in game."""
        if len(word) < MIN_LETTERS_IN_WORD:
            return False
        if word[0] not in self.get_letter_candidates():
            return False
        for prev_index, letter in enumerate(word[1:]):
            if letter not in self.get_letter_candidates(word[prev_index]):
                return False
        return True

    def _add_word_to_words_by_first_letter(self, word: Word) -> None:
        first_letter_group = self._words_by_first_letter.setdefault(
            word.first_letter, {}
        )
        uniques_group = first_letter_group.setdefault(word.unique_letters, [])
        uniques_group.append(word)

    def _add_word_to_words_by_uniques(self, word: Word) -> None:
        uniques_group = self._words_by_uniques.setdefault(word, {})
        first_letter_group = uniques_group.setdefault(word.first_letter, [])
        first_letter_group.append(word)

    def create(self) -> None:
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

    def ordered_by_uniques(self) -> list[Word]:
        words_by_uniques = []
        for first_letters_groups in self._words_by_uniques.values():
            for first_letter_group in first_letters_groups.values():
                for word in first_letter_group:
                    words_by_uniques.append(word)
        return words_by_uniques

    def ordered_by_first_letter(self) -> list[Word]:
        words_by_first_letter = []
        for uniques_groups in self._words_by_first_letter.values():
            for uniques_group in uniques_groups.values():
                for word in uniques_group:
                    words_by_first_letter.append(word)
        return words_by_first_letter
