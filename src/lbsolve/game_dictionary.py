"""Game dictionary and related classes."""

from __future__ import annotations
from collections.abc import Sequence
from pathlib import Path

from lbsolve.type_defs import Letter, UniqueCount


MIN_LETTERS_IN_WORD = 3


class Word:
    """Represents a single dictionary word."""

    _word: str
    first_letter: str
    last_letter: str
    unique_letters: frozenset[Letter]

    def __init__(self, word: str) -> None:
        """
        Args:
          word: A single word.
        """
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
        """
        Given the input words returns class instances.

        Args:
          words: some number of single-word strings.
        """
        return [Word(word) for word in words]


class WordSequence(Sequence):
    """Represents a series of words."""

    _word_sequence: tuple[Word]

    def __init__(self, *words: Word) -> None:
        """
        Args:
          words: The words to insert into the series.
        """
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
    """The dictionary of all valid words for the game. A subset of the input
    dictionary."""

    word_list_file: Path
    letter_groups: tuple[tuple[Letter, 3], 4]
    valid_words: int
    invalid_words: int
    _words_by_first_letter: dict[Letter, dict[UniqueCount, str]]
    _words_by_uniques: dict[UniqueCount, dict[Letter, str]]

    def __init__(
        self, word_list_file: Path, game_letter_groups: tuple[tuple[Letter, 3], 4]
    ) -> None:
        """
        Args:
          word_list_file: The file containing all words to potentially use in the
            game. Each word should be on its own line.
        game_letter_groups: Four tuples, each containing three letters. Each tuple
        represents one side of the "letter box".
        """
        self.word_list_file = word_list_file
        self.letter_groups = self._normalize_letter_groups(game_letter_groups)
        self.valid_words = 0
        self.invalid_words = 0
        self._words_by_first_letter = {}
        self._words_by_uniques = {}

    @staticmethod
    def _normalize_letter_groups(
        letter_groups: tuple[tuple[Letter, 3], 4]
    ) -> tuple[tuple[Letter, 3], 4]:
        """
        Ensures each letter is in a common format.
        Args:
         letter_groups: The letter groups as supplied by the user.

        Returns: The letter groups after normalization.
        """
        normalize_letter_groups = []
        for letter_group in letter_groups:
            normalize_letter_groups.append(
                tuple(letter.lower() for letter in letter_group)
            )
        return tuple(normalize_letter_groups)

    def get_letter_candidates(self, current_letter="") -> list[Letter]:
        """Returns letters on sides of the letter box that don't contain
        the given letter. If no letter is given it returns all letters.

        Args:
          current_letter: The letter who's side should be excluded from the
            letter candidates.

        Returns: Valid letters.
        """
        candidates = []
        for letter_group in self.letter_groups:
            if current_letter in letter_group:
                continue
            candidates.extend(letter_group)
        return candidates

    def word_is_valid(self, word: str) -> bool:
        """Tests that word can be used in game.

        Args:
          word: The word to test.

        Returns: If the word can be used in the game."""
        if len(word) < MIN_LETTERS_IN_WORD:
            return False
        if word[0] not in self.get_letter_candidates():
            return False
        for prev_index, word_letter in enumerate(word[1:]):
            if word_letter not in self.get_letter_candidates(word[prev_index]):
                return False
        return True

    def _add_word_to_words_by_first_letter(self, word: Word) -> None:
        """
        Adds the word to the words-by-first-letter data structure.

        Args:
          word: THe word to add.
        """
        first_letter_group = self._words_by_first_letter.setdefault(
            word.first_letter, {}
        )
        uniques_group = first_letter_group.setdefault(word.unique_letters, [])
        uniques_group.append(word)

    def _add_word_to_words_by_uniques(self, word: Word) -> None:
        """
        Adds the word to the words-by-unique-letters data structure.

        Args:
          word: THe word to add.
        """
        uniques_group = self._words_by_uniques.setdefault(len(word.unique_letters), {})
        first_letter_group = uniques_group.setdefault(word.first_letter, [])
        first_letter_group.append(word)

    def create(self) -> None:
        """Creates the game dictionary."""
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
        """
        Get all words in the game dictionary, ordered by the number of unique
        letters.

        Returns: The list of game words.
        """
        words_by_uniques = []
        for first_letters_groups in self._words_by_uniques.values():
            for first_letter_group in first_letters_groups.values():
                for word in first_letter_group:
                    words_by_uniques.append(word)
        return words_by_uniques

    def ordered_by_first_letter(self) -> list[Word]:
        """
        Get all words in the game dictionary, ordered by the first letter.

        Returns: The list of game words.
        """
        words_by_first_letter = []
        for uniques_groups in self._words_by_first_letter.values():
            for uniques_group in uniques_groups.values():
                for word in uniques_group:
                    words_by_first_letter.append(word)
        return words_by_first_letter

    def get_words_with_first_letter(self, lookup: Letter) -> list[Word]:
        """
        Get all words that start with the given first letter.

        Args:
          lookup: The first letter to use in the search.

        Returns: Matching words.
        """
        words_by_uniques = self._words_by_first_letter.get(lookup, {})
        return [word for words in words_by_uniques.values() for word in words]

    def get_words_with_uniques(self, lookup: UniqueCount) -> list[Word]:
        """
        Get all words that have the given number of unique letters.

        Args:
          lookup: The number of unique letters to use in the search.

        Returns: Matching words.
        """
        words_by_last_letter = self._words_by_uniques.get(lookup, {})
        return [word for words in words_by_last_letter.values() for word in words]
