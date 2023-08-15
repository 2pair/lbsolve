import pytest

from lbsolve.game_dictionary import Word
from lbsolve.solution_finder import SolutionCandidate, SolutionFinder


class TestSolutionCandidate:
    def test_length(self):
        sc = SolutionCandidate()
        sequence = ["cat", "tap", "pat"]
        sc.sequence = sequence
        assert sc.length() == len(sequence)

    def test_add_word_one(self):
        sc = SolutionCandidate()
        word = Word("racecar")
        sc.add_word(word)
        assert sc.sequence == [word]
        assert sc.last_letter == "r"
        assert len(sc.unique_letters) == 4
        assert sc.unique_letters == {"r", "a", "c", "e"}

    def test_add_word_multiple(self):
        sc = SolutionCandidate()
        word_1 = Word("racecar")
        word_2 = Word("react")
        sc.add_word(word_1)
        sc.add_word(word_2)
        assert sc.sequence == [word_1, word_2]
        assert sc.last_letter == "t"
        assert len(sc.unique_letters) == 5
        assert sc.unique_letters == {"r", "a", "c", "e", "t"}

    def test_add_word_value_error(self):
        sc = SolutionCandidate()
        word_1 = Word("racecar")
        word_2 = Word("driver")
        sc.add_word(word_1)
        with pytest.raises(ValueError) as ctx:
            sc.add_word(word_2)
        assert (
            "First letter of new word does not match last letter of last word"
            == str(ctx.value)
        )


class TestSolutionFinder:
    def test_add_to_solutions_list(self):
        pass
