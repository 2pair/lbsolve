import pytest

from lbsolve.game_dictionary import Word, WordSequence
from lbsolve.solution_finder import SolutionCandidate, SolutionFinder


class TestSolutionCandidate:
    def test_length(self):
        sequence = (Word("cat"), Word("tap"), Word("pat"))
        sc = SolutionCandidate(WordSequence(*sequence))
        assert len(sc) == len(sequence)

    def test_clone_and_extend_one(self):
        base_word = Word("rear")
        sc = SolutionCandidate(WordSequence(base_word))
        word = Word("racecar")
        new_sc = sc.clone_and_extend(word)
        assert new_sc.sequence == WordSequence(base_word, word)
        assert new_sc.last_letter == "r"
        assert len(new_sc.unique_letters) == 4
        assert new_sc.unique_letters == {"r", "a", "c", "e"}

    def test_lone_and_extend_multiple(self):
        base_word = Word("rear")
        sc = SolutionCandidate(WordSequence(base_word))
        word_1 = Word("racecar")
        word_2 = Word("react")
        sc_2 = sc.clone_and_extend(word_1)
        sc_3 = sc_2.clone_and_extend(word_2)
        assert sc_3.sequence == WordSequence(base_word, word_1, word_2)
        assert sc_3.last_letter == "t"
        assert len(sc_3.unique_letters) == 5
        assert sc_3.unique_letters == {"r", "a", "c", "e", "t"}

    def test_clone_and_extend_value_error(self):
        sc = SolutionCandidate(WordSequence(Word("racecar")))
        with pytest.raises(ValueError) as ctx:
            sc.clone_and_extend(Word("driver"))
        assert (
            "First letter of new word does not match last letter of last word"
            == str(ctx.value)
        )


class TestCandidateMap:
    def test_insert(self):
        pass


class TestSolutionList:
    def test_insert(self):
        pass


class TestSolutionFinder:
    def test_get_solutions(self):
        pass
