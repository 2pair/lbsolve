import pytest

from lbsolve.game_dictionary import GameDictionary, Word, WordSequence
from lbsolve.solution_finder import (
    CandidateMap,
    SolutionCandidate,
    SolutionFinder,
    SolutionList,
)

CANDIDATES = [
    SolutionCandidate(WordSequence(Word("cat"), Word("tap"), Word("pat"))),
    SolutionCandidate(WordSequence(Word("rap"), Word("par"), Word("rat"))),
    SolutionCandidate(WordSequence(Word("car"), Word("rig"), Word("gal"))),
    SolutionCandidate(WordSequence(Word("car"), Word("rip"), Word("pat"))),
]

SOLUTIONS = [
    SolutionCandidate(WordSequence(Word("consequential"), Word("lap"))),
    SolutionCandidate(WordSequence(Word("forgiver"), Word("reconciliation"))),
    SolutionCandidate(WordSequence(Word("visited"), Word("doctor"), Word("rash"))),
]


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
    def test_insert(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        assert cm.count == 1
        assert cm.candidates_by_uniques_by_last_letter["t"][4] == [CANDIDATES[0]]
        assert cm.candidates_by_last_letter_by_uniques[4]["t"] == [CANDIDATES[0]]
        cm.insert(CANDIDATES[1])
        assert cm.count == 2
        assert cm.candidates_by_uniques_by_last_letter["t"][4] == [
            CANDIDATES[0],
            CANDIDATES[1],
        ]
        assert cm.candidates_by_last_letter_by_uniques[4]["t"] == [
            CANDIDATES[0],
            CANDIDATES[1],
        ]

    def test_len(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        assert len(cm) == 1

    def test_iter(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        cm.insert(CANDIDATES[1])
        for index, candidate in enumerate(cm):
            assert candidate == CANDIDATES[index]

    def test_getitem_by_letter(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        cm.insert(CANDIDATES[2])
        assert cm["t"] == {4: [CANDIDATES[0]]}
        assert cm["l"] == {6: [CANDIDATES[2]]}

    def test_getitem_by_uniques(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        cm.insert(CANDIDATES[2])
        assert cm[4] == {"t": [CANDIDATES[0]]}
        assert cm[6] == {"l": [CANDIDATES[2]]}

    def test_getitem_by_letter_and_uniques(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        cm.insert(CANDIDATES[2])
        cm.insert(CANDIDATES[3])
        assert cm["t", 4] == [CANDIDATES[0]]
        assert cm["l", 6] == [CANDIDATES[2]]
        assert cm["t", 6] == [CANDIDATES[3]]

    def test_getitem_by_uniques_and_letters(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        cm.insert(CANDIDATES[2])
        cm.insert(CANDIDATES[3])
        assert cm[4, "t"] == [CANDIDATES[0]]
        assert cm[6, "l"] == [CANDIDATES[2]]
        assert cm[6, "t"] == [CANDIDATES[3]]

    def test_getitem_by_invalid(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
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
        cm1.insert(CANDIDATES[0])
        cm1.insert(CANDIDATES[1])
        cm2 = CandidateMap()
        cm2.insert(CANDIDATES[2])
        cm2.insert(CANDIDATES[3])
        cm1.merge(cm2)
        assert len(cm1) == 4
        for index, candidate in enumerate(cm1):
            assert candidate == CANDIDATES[index]


class TestSolutionList:
    def test_insert_maintaining_order(self):
        sl = SolutionList()
        sl.insert(SOLUTIONS[2])
        assert list(sl.solutions_by_words.keys())[0] == 3
        sl.insert(SOLUTIONS[0])
        assert list(sl.solutions_by_words.keys())[0] == 2
        assert list(sl.solutions_by_words.keys())[1] == 3

    def test_insert(self):
        sl = SolutionList()
        sl.insert(SOLUTIONS[0])
        assert sl.count == 1
        assert sl.solutions_by_words[2] == [SOLUTIONS[0]]
        sl.insert(SOLUTIONS[1])
        assert sl.count == 2
        assert sl.solutions_by_words[2] == [
            SOLUTIONS[0],
            SOLUTIONS[1],
        ]
        sl.insert(SOLUTIONS[2])
        assert sl.count == 3
        assert sl.solutions_by_words[3] == [SOLUTIONS[2]]

    def test_flatter(self):
        sl = SolutionList()
        sl.insert(SOLUTIONS[0])
        sl.insert(SOLUTIONS[1])
        sl.insert(SOLUTIONS[2])
        solutions = sl.flatten()
        assert isinstance(solutions, list)
        for index, solution in enumerate(solutions):
            assert solution == SOLUTIONS[index]

    def test_getitem(self):
        sl = SolutionList()
        sl.insert(SOLUTIONS[0])
        sl.insert(SOLUTIONS[1])
        assert sl[2] == [SOLUTIONS[0], SOLUTIONS[1]]
        assert sl[2, 1] == SOLUTIONS[1]

    def test_getitem_invalid(self):
        sl = SolutionList()
        sl.insert(SOLUTIONS[0])
        with pytest.raises(LookupError) as ctx:
            sl[{"dogs!"}]
            assert "Provided key type is not valid." == str(ctx.value)

    def test_iter(self):
        sl = SolutionList()
        sl.insert(SOLUTIONS[2])
        sl.insert(SOLUTIONS[0])
        sl.insert(SOLUTIONS[1])
        for index, solution in enumerate(sl):
            assert solution == SOLUTIONS[index]

    def test_len(self):
        sl = SolutionList()
        sl.insert(SOLUTIONS[2])
        sl.insert(SOLUTIONS[0])
        assert len(sl) == 2


class TestSolutionFinder:
    @pytest.fixture
    def mock_game_dictionary(self, mocker):
        return mocker.patch("lbsolve.solution_finder.GameDictionary")

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
        mock_start = mocker.patch("lbsolve.solution_finder.Thread.start")
        sf = SolutionFinder(mock_game_dictionary)
        sf.start()
        assert mock_start.called_once()

    def test_stop_and_join(self, mocker, mock_game_dictionary):
        mock_join = mocker.patch("lbsolve.solution_finder.Thread.join")
        sf = SolutionFinder(mock_game_dictionary)
        sf.stop(join=True)
        mock_join.assert_called_once_with(10)
        assert sf._thread_should_stop is True

    def test_stop_and_return(self, mocker, mock_game_dictionary):
        mock_join = mocker.patch("lbsolve.solution_finder.Thread.join")
        sf = SolutionFinder(mock_game_dictionary)
        sf.stop(join=False)
        assert not mock_join.called
        assert sf._thread_should_stop is True

    def test_running(self, mocker, mock_game_dictionary):
        mock_is_alive = mocker.patch("lbsolve.solution_finder.Thread.is_alive")
        mock_is_alive.return_value = True
        sf = SolutionFinder(mock_game_dictionary)
        running = sf.running()
        assert running is True
        assert mock_is_alive.called_once()

    def test_get_solutions(self, mock_game_dictionary):
        sf = SolutionFinder(mock_game_dictionary)
        sf.solutions = SolutionList()
        sf.solutions.insert(SOLUTIONS[0])
        sf.solutions.insert(SOLUTIONS[2])
        solutions = sf.get_solutions()
        assert len(solutions) == 2
        assert solutions is not sf.solutions
        assert solutions[2][0] == SOLUTIONS[0]
        assert sf.solutions.solutions_by_words[2][0] is SOLUTIONS[0]
        assert solutions[2][0] is not sf.solutions.solutions_by_words[2][0]

    def test__add_new_solutions(self, mocker, mock_game_dictionary):
        mock_print = mocker.patch("builtins.print")
        sf = SolutionFinder(mock_game_dictionary)
        sf._add_new_solution(SOLUTIONS[0])
        assert len(sf.solutions) == 1
        assert sf.solutions[2][0] == SOLUTIONS[0]
        mock_print.assert_called_once_with(
            f"Found new solution: "
            f"{' - '.join([str(word) for word in sf.solutions[2][0].sequence])}"
        )

    def test_add_word_to_solution_candidates(self):
        cm = CandidateMap()
        cm.insert(CANDIDATES[0])
        cm.insert(CANDIDATES[1])
        new_word = Word("trajectory")
        new_candidates = SolutionFinder._add_word_to_solution_candidates(cm, new_word)
        for index, candidate in enumerate(new_candidates):
            initial_word_sequence = CANDIDATES[index].sequence._word_sequence
            new_word_sequence = candidate.sequence._word_sequence
            assert new_word_sequence == initial_word_sequence + (new_word,)
