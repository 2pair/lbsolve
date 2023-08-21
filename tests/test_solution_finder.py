import pytest

from lbsolve.game_dictionary import GameDictionary, Word, WordSequence
from lbsolve.solution_finder import (
    CandidateMap,
    SolutionCandidate,
    SolutionFinder,
    SolutionList,
)


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

    def test_eq(self):
        sequence = (Word("cat"), Word("tap"), Word("pat"))
        sc1 = SolutionCandidate(WordSequence(*sequence))
        sc2 = SolutionCandidate(WordSequence(*sequence))
        assert sc1 == sc2
        assert sc1 is not sc2


class TestCandidateMap:
    candidates = [
        SolutionCandidate(WordSequence(Word("cat"), Word("tap"), Word("pat"))),
        SolutionCandidate(WordSequence(Word("rap"), Word("par"), Word("rat"))),
        SolutionCandidate(WordSequence(Word("car"), Word("rig"), Word("gal"))),
        SolutionCandidate(WordSequence(Word("car"), Word("rip"), Word("pat"))),
    ]

    def test_insert(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        assert cm.count == 1
        assert cm.candidates_by_uniques_by_last_letter["t"][4] == [self.candidates[0]]
        assert cm.candidates_by_last_letter_by_uniques[4]["t"] == [self.candidates[0]]
        cm.insert(self.candidates[1])
        assert cm.count == 2
        assert cm.candidates_by_uniques_by_last_letter["t"][4] == [
            self.candidates[0],
            self.candidates[1],
        ]
        assert cm.candidates_by_last_letter_by_uniques[4]["t"] == [
            self.candidates[0],
            self.candidates[1],
        ]

    def test_len(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        assert len(cm) == 1

    def test_iter(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        cm.insert(self.candidates[1])
        for index, candidate in enumerate(cm):
            assert candidate == self.candidates[index]

    def test_getitem_by_letter(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        cm.insert(self.candidates[2])
        assert cm["t"] == {4: [self.candidates[0]]}
        assert cm["l"] == {6: [self.candidates[2]]}

    def test_getitem_by_uniques(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        cm.insert(self.candidates[2])
        assert cm[4] == {"t": [self.candidates[0]]}
        assert cm[6] == {"l": [self.candidates[2]]}

    def test_getitem_by_letter_and_uniques(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        cm.insert(self.candidates[2])
        cm.insert(self.candidates[3])
        assert cm["t", 4] == [self.candidates[0]]
        assert cm["l", 6] == [self.candidates[2]]
        assert cm["t", 6] == [self.candidates[3]]

    def test_getitem_by_uniques_and_letters(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        cm.insert(self.candidates[2])
        cm.insert(self.candidates[3])
        assert cm[4, "t"] == [self.candidates[0]]
        assert cm[6, "l"] == [self.candidates[2]]
        assert cm[6, "t"] == [self.candidates[3]]

    def test_getitem_by_invalid(self):
        cm = CandidateMap()
        cm.insert(self.candidates[0])
        with pytest.raises(LookupError) as ctx:
            cm[2.3]
            assert "Provided key type is not valid." == str(ctx.value)
        with pytest.raises(LookupError) as ctx:
            cm[1, 2]
            assert "Provided key type is not valid." == str(ctx.value)
        with pytest.raises(LookupError) as ctx:
            cm["t", "l"]
            assert "Provided key type is not valid." == str(ctx.value)

    def test_merge(self):
        cm1 = CandidateMap()
        cm1.insert(self.candidates[0])
        cm1.insert(self.candidates[1])
        cm2 = CandidateMap()
        cm2.insert(self.candidates[2])
        cm2.insert(self.candidates[3])
        cm1.merge(cm2)
        assert len(cm1) == 4
        for index, candidate in enumerate(cm1):
            assert candidate == self.candidates[index]


class TestSolutionList:
    solutions = [
        SolutionCandidate(WordSequence(Word("consequential"), Word("lap"))),
        SolutionCandidate(WordSequence(Word("forgiver"), Word("reconciliation"))),
        SolutionCandidate(WordSequence(Word("visited"), Word("doctor"), Word("rash"))),
    ]

    def test_insert_maintaining_order(self):
        sl = SolutionList()
        sl.insert(self.solutions[2])
        assert list(sl.solutions_by_words.keys())[0] == 3
        sl.insert(self.solutions[0])
        assert list(sl.solutions_by_words.keys())[0] == 2
        assert list(sl.solutions_by_words.keys())[1] == 3
       

    def test_insert(self):
        sl = SolutionList()
        sl.insert(self.solutions[0])
        assert sl.count == 1
        assert sl.solutions_by_words[2] == [self.solutions[0]]
        sl.insert(self.solutions[1])
        assert sl.count == 2
        assert sl.solutions_by_words[2] == [
            self.solutions[0],
            self.solutions[1],
        ]
        sl.insert(self.solutions[2])
        assert sl.count == 3
        assert sl.solutions_by_words[3] == [self.solutions[2]]

    def test_getitem(self):
        sl = SolutionList()
        sl.insert(self.solutions[0])
        sl.insert(self.solutions[1])
        assert sl[2] == [self.solutions[0], self.solutions[1]]
        assert sl[2, 1] == self.solutions[1]

    def test_getitem_invalid(self):
        sl = SolutionList()
        sl.insert(self.solutions[0])
        with pytest.raises(LookupError) as ctx:
            sl[{"dogs!"}]
            assert "Provided key type is not valid." == str(ctx.value)

    def test_iter(self):
        sl = SolutionList()
        sl.insert(self.solutions[2])
        sl.insert(self.solutions[0])
        sl.insert(self.solutions[1])
        for index, solution in enumerate(sl):
            assert solution == self.solutions[index]

    def test_len(self):
        sl = SolutionList()
        sl.insert(self.solutions[2])
        sl.insert(self.solutions[0])
        assert len(sl) == 2     


class TestSolutionFinder:

    @pytest.fixture
    def mock_game_dictionary(self, mocker):
        return mocker.patch(
            "lbsolve.solution_finder.GameDictionary"
        )

    def test__seed_candidates(self, monkeypatch):
        mock_dictionary = [Word("spoil"), Word("milk"), Word("jug")]
        def mock_obu():
            return mock_dictionary
        
        gd = GameDictionary("file", "letters")
        monkeypatch.setattr(gd, "ordered_by_uniques", mock_obu)
        sf = SolutionFinder(gd)
        new_candidates = sf._seed_candidates()
        assert len(new_candidates) == 3
        for index, candidate in enumerate(new_candidates):
            assert isinstance(candidate, SolutionCandidate)
            assert len(candidate) == 1
            assert candidate.sequence[0] == mock_dictionary[index]

    def test_start(self, mocker, mock_game_dictionary):
        mock_start = mocker.patch(
            "lbsolve.solution_finder.Thread.start"
            )
        sf = SolutionFinder(mock_game_dictionary)
        sf.start()
        assert mock_start.called_once()

    def test_stop_and_join(self, mocker, mock_game_dictionary):
        mock_join = mocker.patch(
            "lbsolve.solution_finder.Thread.join"
            )
        sf = SolutionFinder(mock_game_dictionary)
        sf.stop()
        assert mock_join.called_once_with(10)
        assert sf._thread_should_stop == True

    def test_stop_and_return(self, mocker, mock_game_dictionary):
        mock_join = mocker.patch(
            "lbsolve.solution_finder.Thread.join"
            )
        sf = SolutionFinder(mock_game_dictionary)
        sf.stop(join=False)
        assert not mock_join.called
        assert sf._thread_should_stop == True

    def test_running(self, mocker, mock_game_dictionary):
        mock_is_alive = mocker.patch(
            "lbsolve.solution_finder.Thread.is_alive"
            )
        mock_is_alive.return_value = True
        sf = SolutionFinder(mock_game_dictionary)
        running = sf.running()
        assert running == True
        assert mock_is_alive.called_once()

        

