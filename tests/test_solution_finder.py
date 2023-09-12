import pytest

from lbsolve.game_dictionary import Word, WordSequence
from lbsolve.solution_finder import (
    PartialSolutionMap,
    PartialSolution,
    SolutionFinder,
    SolutionList,
)


@pytest.fixture
def candidates():
    return (
        PartialSolution(WordSequence(*Word.factory("cat", "tap", "pat"))),
        PartialSolution(WordSequence(*Word.factory("rap", "par", "rat"))),
        PartialSolution(WordSequence(*Word.factory("car", "rig", "gal"))),
        PartialSolution(WordSequence(*Word.factory("car", "rip", "pat"))),
    )


@pytest.fixture
def solutions():
    return (
        PartialSolution(WordSequence(*Word.factory("consequential", "lap"))),
        PartialSolution(WordSequence(*Word.factory("forgiver", "reconciliation"))),
        PartialSolution(WordSequence(*Word.factory("visited", "doctor", "rash"))),
    )


class TestPartialSolution:
    def test_length(self):
        sequence = Word.factory("cat", "tap", "pat")
        sc = PartialSolution(WordSequence(*sequence))
        assert len(sc) == len(sequence)

    def test_clone_and_extend_one(self):
        base_word = Word("rear")
        sc = PartialSolution(WordSequence(base_word))
        word = Word("racecar")
        new_sc = sc.clone_and_extend(word)
        assert new_sc.sequence == WordSequence(base_word, word)
        assert new_sc.last_letter == "r"
        assert len(new_sc.unique_letters) == 4
        assert new_sc.unique_letters == {"r", "a", "c", "e"}

    def test_lone_and_extend_multiple(self):
        base_word = Word("rear")
        sc = PartialSolution(WordSequence(base_word))
        word_1 = Word("racecar")
        word_2 = Word("react")
        sc_2 = sc.clone_and_extend(word_1)
        sc_3 = sc_2.clone_and_extend(word_2)
        assert sc_3.sequence == WordSequence(base_word, word_1, word_2)
        assert sc_3.last_letter == "t"
        assert len(sc_3.unique_letters) == 5
        assert sc_3.unique_letters == {"r", "a", "c", "e", "t"}

    def test_clone_and_extend_value_error(self):
        sc = PartialSolution(WordSequence(Word("racecar")))
        with pytest.raises(ValueError) as ctx:
            sc.clone_and_extend(Word("driver"))
        assert (
            "First letter of new word does not match last letter of last word"
            == str(ctx.value)
        )

    def test_eq(self):
        sequence = Word.factory("cat", "tap", "pat")
        sc1 = PartialSolution(WordSequence(*sequence))
        sc2 = PartialSolution(WordSequence(*sequence))
        assert sc1 == sc2
        assert sc1 is not sc2

    def test_to_str(self):
        words = ["cake", "eating", "guy"]
        sc = PartialSolution(WordSequence(*Word.factory(*words)))
        assert str(sc) == "-".join(words)


class TestPartialSolutionMap:
    def test_insert(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        assert ps.count == 1
        assert ps.candidates_by_uniques_by_last_letter["t"][4] == [candidates[0]]
        assert ps.candidates_by_last_letter_by_uniques[4]["t"] == [candidates[0]]
        ps.insert(candidates[1])
        assert ps.count == 2
        assert ps.candidates_by_uniques_by_last_letter["t"][4] == [
            candidates[0],
            candidates[1],
        ]
        assert ps.candidates_by_last_letter_by_uniques[4]["t"] == [
            candidates[0],
            candidates[1],
        ]

    def test_len(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        assert len(ps) == 1

    def test_iter(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        ps.insert(candidates[1])
        for index, candidate in enumerate(ps):
            assert candidate == candidates[index]

    def test_getitem_by_letter(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        ps.insert(candidates[2])
        assert ps["t"] == [candidates[0]]
        assert ps["l"] == [candidates[2]]

    def test_getitem_by_uniques(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        ps.insert(candidates[2])
        assert ps[4] == [candidates[0]]
        assert ps[6] == [candidates[2]]

    def test_getitem_by_letter_and_uniques(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        ps.insert(candidates[2])
        ps.insert(candidates[3])
        assert ps["t", 4] == [candidates[0]]
        assert ps["l", 6] == [candidates[2]]
        assert ps["t", 6] == [candidates[3]]

    def test_getitem_by_uniques_and_letters(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        ps.insert(candidates[2])
        ps.insert(candidates[3])
        assert ps[4, "t"] == [candidates[0]]
        assert ps[6, "l"] == [candidates[2]]
        assert ps[6, "t"] == [candidates[3]]

    def test_getitem_by_invalid(self, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        with pytest.raises(LookupError) as ctx:
            ps[2.3]
            assert "Provided key type is not valid." == str(ctx.value)
        with pytest.raises(LookupError) as ctx:
            ps[1, 2]
            assert "Provided key type is not valid." == str(ctx.value)
        with pytest.raises(LookupError) as ctx:
            ps["t", "l"]
            assert "Provided key type is not valid." == str(ctx.value)

    def test_merge_candidate_map(self, candidates):
        cm1 = PartialSolutionMap()
        cm1.insert(candidates[0])
        cm1.insert(candidates[1])
        cm2 = PartialSolutionMap()
        cm2.insert(candidates[2])
        cm2.insert(candidates[3])
        cm1.merge(cm2)
        assert len(cm1) == 4
        for index, candidate in enumerate(cm1):
            assert candidate == candidates[index]

    def test_merge_candidate_map_duplicates(self, candidates):
        cm1 = PartialSolutionMap()
        cm1.insert(candidates[0])
        cm2 = PartialSolutionMap()
        cm2.insert(candidates[0])
        cm2.insert(candidates[1])
        cm1.merge(cm2)
        assert len(cm1) == 2
        for index, candidate in enumerate(cm1):
            assert candidate == candidates[index]

    def test_merge_list(self, candidates):
        candidate_list = [candidates[0], candidates[1]]
        ps = PartialSolutionMap()
        ps.merge(candidate_list)
        assert len(ps) == 2
        for index, candidate in enumerate(ps):
            assert candidate == candidates[index]


class TestSolutionList:
    def test_insert_maintaining_order(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[2])
        assert list(sl.solutions_by_words.keys())[0] == 3
        sl.insert(solutions[0])
        assert list(sl.solutions_by_words.keys())[0] == 2
        assert list(sl.solutions_by_words.keys())[1] == 3

    def test_insert(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[0])
        assert sl.count == 1
        assert sl.solutions_by_words[2] == [solutions[0]]
        sl.insert(solutions[1])
        assert sl.count == 2
        assert sl.solutions_by_words[2] == [
            solutions[0],
            solutions[1],
        ]
        sl.insert(solutions[2])
        assert sl.count == 3
        assert sl.solutions_by_words[3] == [solutions[2]]

    def test_flatten(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[0])
        sl.insert(solutions[1])
        sl.insert(solutions[2])
        solutions = sl.flatten()
        assert isinstance(solutions, list)
        for index, solution in enumerate(solutions):
            assert solution == solutions[index]

    def test_getitem(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[0])
        sl.insert(solutions[1])
        assert sl[2] == [solutions[0], solutions[1]]
        assert sl[2, 1] == solutions[1]

    def test_getitem_invalid(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[0])
        with pytest.raises(LookupError) as ctx:
            sl[{"dogs!"}]
            assert "Provided key type is not valid." == str(ctx.value)

    def test_contains(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[0])
        assert solutions[0] in sl
        assert solutions[1] not in sl

    def test_iter(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[2])
        sl.insert(solutions[0])
        sl.insert(solutions[1])
        for index, solution in enumerate(sl):
            assert solution == solutions[index]

    def test_len(self, solutions):
        sl = SolutionList()
        sl.insert(solutions[2])
        sl.insert(solutions[0])
        assert len(sl) == 2

    def test_eq(self, solutions):
        solution_lists = []
        for i in range(2):
            sl = SolutionList()
            sl.insert(solutions[2])
            sl.insert(solutions[0])
            solution_lists.append(sl)
        assert solution_lists[0] == solution_lists[1]
        assert solution_lists[0] is not solution_lists[1]


class TestSolutionFinder:
    @pytest.fixture
    def mock_game_dictionary(self, mocker):
        m_dictionary = mocker.patch("lbsolve.solution_finder.GameDictionary")
        m_dictionary.get_letter_candidates.return_value = [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
        ]  # only care about the list length here
        return m_dictionary

    def test__seed_candidates(self, mock_game_dictionary):
        mock_dictionary = [Word("jug"), Word("milk"), Word("spoil")]
        mock_game_dictionary.ordered_by_first_letter.return_value = mock_dictionary
        sf = SolutionFinder(mock_game_dictionary)
        new_candidates = sf._seed_candidates()
        assert len(new_candidates) == 3
        for index, candidate in enumerate(new_candidates):
            assert isinstance(candidate, PartialSolution)
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

    def test_solution_count(self, solutions, mock_game_dictionary):
        sf = SolutionFinder(mock_game_dictionary)
        sf.solutions = SolutionList()
        sf.solutions.insert(solutions[0])
        sf.solutions.insert(solutions[2])
        count = sf.solutions_count()
        assert count == 2

    def test_get_solutions(self, solutions, mock_game_dictionary):
        sf = SolutionFinder(mock_game_dictionary)
        sf.solutions = SolutionList()
        sf.solutions.insert(solutions[0])
        sf.solutions.insert(solutions[2])
        new_solutions = sf.get_solutions()
        assert len(new_solutions) == 2
        assert new_solutions[2][0] == solutions[0]
        assert new_solutions is not sf.solutions
        assert sf.solutions.solutions_by_words[2][0] is solutions[0]
        assert new_solutions[2][0] is not sf.solutions.solutions_by_words[2][0]

    def test__add_new_solutions(self, solutions, mocker, mock_game_dictionary):
        mock_print = mocker.patch("builtins.print")
        sf = SolutionFinder(mock_game_dictionary)
        sf._add_new_solution(solutions[0])
        assert len(sf.solutions) == 1
        assert sf.solutions[2][0] == solutions[0]
        mock_print.assert_called_once_with(
            f"Found new solution: "
            f"{' - '.join([str(word) for word in sf.solutions[2][0].sequence])}"
        )

    def test_add_word_to_solution_candidates(self, solutions, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        ps.insert(candidates[1])
        new_word = Word("trajectory")
        new_candidates = SolutionFinder._add_word_to_solution_candidates(ps, new_word)
        for index, candidate in enumerate(new_candidates):
            initial_word_sequence = candidates[index].sequence._word_sequence
            new_word_sequence = candidate.sequence._word_sequence
            assert new_word_sequence == initial_word_sequence + (new_word,)

    def test_add_word_to_solution_candidates_twice(self, solutions, candidates):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        new_word = Word("trot")
        new_candidates = SolutionFinder._add_word_to_solution_candidates(ps, new_word)
        initial_word_sequence = candidates[0].sequence._word_sequence
        candidates_by_uniques = new_candidates["t"]
        new_word_sequence = candidates_by_uniques[0].sequence._word_sequence
        assert new_word_sequence == initial_word_sequence + (new_word,)
        no_candidates = SolutionFinder._add_word_to_solution_candidates(
            new_candidates, new_word
        )
        assert len(no_candidates) == 0

    def test__promote_candidates(self, candidates, solutions, mock_game_dictionary):
        ps = PartialSolutionMap()
        ps.insert(candidates[0])
        ps.insert(solutions[0])
        ps.insert(solutions[1])
        sf = SolutionFinder(mock_game_dictionary)
        new_solutions = sf._promote_candidates(ps)
        assert len(new_solutions) == 2
        assert candidates[0] not in new_solutions
        for index, solution in enumerate(new_solutions):
            assert solution == solutions[index]

    def test__promote_candidates_duplicates(self, solutions, mock_game_dictionary):
        cm1 = PartialSolutionMap()
        cm1.insert(solutions[0])
        cm1.insert(solutions[1])
        sf = SolutionFinder(mock_game_dictionary)
        new_solutions = sf._promote_candidates(cm1)
        assert len(new_solutions) == 2
        assert len(sf.solutions) == 2
        cm2 = PartialSolutionMap()
        cm2.insert(solutions[0])
        cm2.insert(solutions[1])
        new_solutions = sf._promote_candidates(cm1)
        assert len(new_solutions) == 0
        assert len(sf.solutions) == 2

    def test__mutate_solution_candidates(self, mock_game_dictionary):
        word_list = [
            "car",
            "care",
            "cold",
            "could",
            "dare",
            "drain",
            "end",
            "noun",
            "nearby",
        ]
        # Shortest solution: could -> drain -> nearby
        # Longest solution:  cold|could -> dare  -> end -> drain -> noun -> nearby
        words = Word.factory(*word_list)
        mock_game_dictionary.ordered_by_first_letter.return_value = words
        sf = SolutionFinder(mock_game_dictionary)
        sf._solution_candidates = sf._seed_candidates()
        assert len(sf._solution_candidates) == len(word_list)
        sf._mutate_solution_candidates()
        assert len(sf._solution_candidates) == 20
        assert len(sf.solutions) == 0
        generation = 1
        final_candidate_count = 0
        last_candidate_count = 0
        while True:
            sf._mutate_solution_candidates()
            generation += 1
            assert len(sf._solution_candidates) >= last_candidate_count
            last_candidate_count = len(sf._solution_candidates)
            if generation == 2:
                assert len(sf.solutions) == 1
                assert str(sf.solutions[3, 0]) == "could-drain-nearby"
            if generation == len(word_list):
                final_candidate_count = len(sf._solution_candidates)
            if generation > len(word_list):
                assert final_candidate_count == last_candidate_count
                if generation == len(word_list) + 2:
                    break
        assert max(sf.solutions.solutions_by_words.keys()) == 6
        assert min(sf.solutions.solutions_by_words.keys()) == 3

    def test__find_solutions_breadth_first(self, mocker, mock_game_dictionary):
        calls = 0
        solution_at_call = 5

        def mock_solutions():
            nonlocal calls
            while True:
                calls += 1
                yield 1 if solution_at_call == calls else 0

        mocker.patch("lbsolve.solution_finder.SolutionFinder._seed_candidates")
        mock_mutate = mocker.patch(
            "lbsolve.solution_finder.SolutionFinder._mutate_solution_candidates"
        )
        mock_mutate.side_effect = mock_solutions()
        sf = SolutionFinder(mock_game_dictionary)
        sf._thread_should_stop = False
        sf._find_solutions_breadth_first()
        assert calls == solution_at_call + 1

    def test__find_solutions_breadth_first_max_depth(
        self, mocker, mock_game_dictionary
    ):
        calls = 0

        def mock_solutions():
            nonlocal calls
            while True:
                calls += 1
                yield 0

        mocker.patch("lbsolve.solution_finder.SolutionFinder._seed_candidates")
        mock_mutate = mocker.patch(
            "lbsolve.solution_finder.SolutionFinder._mutate_solution_candidates"
        )
        mock_mutate.side_effect = mock_solutions()
        sf = SolutionFinder(mock_game_dictionary)
        sf._thread_should_stop = False
        sf.max_depth = 5
        sf._find_solutions_breadth_first()
        assert calls == sf.max_depth

    def test__find_solutions_breadth_first_should_stop(
        self, mocker, mock_game_dictionary
    ):
        calls = 0
        sf = SolutionFinder(mock_game_dictionary)

        def mock_solutions():
            nonlocal calls
            nonlocal sf
            while True:
                calls += 1
                if calls == 10:
                    sf._thread_should_stop = True
                yield 0

        mocker.patch("lbsolve.solution_finder.SolutionFinder._seed_candidates")
        mock_mutate = mocker.patch(
            "lbsolve.solution_finder.SolutionFinder._mutate_solution_candidates"
        )
        mock_mutate.side_effect = mock_solutions()
        sf._thread_should_stop = False
        sf._find_solutions_breadth_first()
        assert calls == 10
