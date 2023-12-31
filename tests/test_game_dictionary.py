from copy import deepcopy
import pytest

from lbsolve.game_dictionary import GameDictionary, Word, WordSequence


class TestWord:
    def test_init(self):
        word = Word("booboo")
        assert word._word == "booboo"
        assert word.first_letter == "b"
        assert word.last_letter == "o"
        assert word.unique_letters == {"b", "o"}

    def test_wrong_type_init(self):
        with pytest.raises(TypeError) as ctx:
            Word(["w", "r", "o", "n", "g"])
        assert "'word' should be type 'str', not 'list'." == str(ctx.value)

    def test_to_str(self):
        raw_word = "pleasant"
        word = Word(raw_word)
        assert str(word) == raw_word

    def test_to_repr(self):
        raw_word = "ferocious"
        word = Word(raw_word)
        assert repr(word) == f"Word({raw_word})"

    def test_eq(self):
        word = Word("soliloquy")
        word_copy = deepcopy(word)
        assert word == word_copy

    def test_factory(self):
        rocket, ship = Word.factory("rocket", "ship")
        assert isinstance(rocket, Word)
        assert str(rocket) == "rocket"
        assert isinstance(ship, Word)
        assert str(ship) == "ship"


class TestWordSequence:
    def test_empty_init(self):
        with pytest.raises(IndexError) as ctx:
            WordSequence()
        assert "One or more word expected." == str(ctx.value)

    def test_wrong_type_init(self):
        with pytest.raises(TypeError) as ctx:
            WordSequence("wrong", "types")
        assert "'words' should be instances of type 'Word', not 'str'." == str(
            ctx.value
        )

    def test_init(self):
        words = Word.factory("big", "dirty", "stinking", "bass")
        word_sequence = WordSequence(*words)
        assert word_sequence._word_sequence == tuple(words)

    def test_len(self):
        words = Word.factory("regrets", "look", "like", "texts")
        word_sequence = WordSequence(*words)
        assert len(word_sequence) == 4

    def test_get_item(self):
        words = Word.factory("neighbors", "that", "should", "be", "friends")
        word_sequence = WordSequence(*words)
        assert word_sequence[0] == Word("neighbors")
        assert word_sequence[-1] == Word("friends")
        assert word_sequence[1:3] == (Word("that"), Word("should"))

    def test_iter(self):
        words = Word.factory("let", "mom", "sleep")
        word_sequence = WordSequence(*words)
        for index, word in enumerate(word_sequence):
            assert word == words[index]

    def test_in(self):
        words = Word.factory("no", "sleep", "remix")
        word_sequence = WordSequence(*words)
        for word in words:
            assert word in word_sequence

    def test_equal(self):
        sequence = (Word("cat"), Word("tap"), Word("pat"))
        word_sequence = WordSequence(*sequence)
        word_sequence_copy = deepcopy(word_sequence)
        assert word_sequence == word_sequence_copy

    def test_to_str(self):
        words = ["realistic", "canopy", "yank"]
        sequence = Word.factory(*words)
        word_sequence = WordSequence(*sequence)
        str(word_sequence) == "-".join(words)


class TestGameDictionary:
    def test_normalize_letter_groups(self):
        letter_groups = (("A", "B", "C"), ("D", "E", "F"))
        normalized = GameDictionary._normalize_letter_groups(letter_groups)
        assert normalized == (("a", "b", "c"), ("d", "e", "f"))

    def test_get_letter_candidates_all(self):
        letter_groups = (("a", "b", "c"), ("d", "e", "f"))
        gd = GameDictionary("", letter_groups)
        candidates = gd.get_letter_candidates()
        assert candidates == ["a", "b", "c", "d", "e", "f"]

    def test_get_letter_candidates_other_sides(self):
        letter_groups = (("a", "b", "c"), ("d", "e", "f"), ("g", "h", "i"))
        gd = GameDictionary("", letter_groups)
        candidates = gd.get_letter_candidates("g")
        assert candidates == ["a", "b", "c", "d", "e", "f"]
        candidates = gd.get_letter_candidates("a")
        assert candidates == ["d", "e", "f", "g", "h", "i"]

    def test_word_is_valid_invalid_letters(self):
        letter_groups = (
            ("a", "b", "c"),
            ("d", "e", "f"),
            ("g", "h", "i"),
            ("j", "k", "l"),
        )
        gd = GameDictionary("", letter_groups)
        assert gd.word_is_valid("") is False
        assert gd.word_is_valid("\t") is False
        assert gd.word_is_valid("pat") is False
        assert gd.word_is_valid("sat") is False
        assert gd.word_is_valid("rat") is False

    def test_word_is_valid_collocated_letters(self):
        letter_groups = (
            ("a", "b", "c"),
            ("d", "e", "f"),
            ("g", "h", "i"),
            ("j", "k", "l"),
        )
        gd = GameDictionary("", letter_groups)
        assert gd.word_is_valid("bat") is False
        assert gd.word_is_valid("hide") is False
        assert gd.word_is_valid("lack") is False

    def test_word_is_valid_true(self):
        letter_groups = (
            ("a", "b", "c"),
            ("d", "e", "f"),
            ("g", "h", "i"),
            ("j", "k", "l"),
        )
        gd = GameDictionary("", letter_groups)
        assert gd.word_is_valid("beg") is True
        assert gd.word_is_valid("head") is True
        assert gd.word_is_valid("lead") is True

    def test__add_word_to_words_by_first_letter(self):
        pass

    def test_create_from_file_all_good(self, monkeypatch, tmp_path):
        tmp_file = tmp_path / "test_dic.txt"
        tmp_file.write_text("apple\nbanana\ncherry\ndate\n")

        def mock_word_is_valid(_mSelf, _word):
            return True

        def mock___add_word_to_words_by_first_letter(_mSelf, _word):
            pass

        def mock__add_word_to_words_by_uniques(_mSelf, _word):
            pass

        monkeypatch.setattr(GameDictionary, "word_is_valid", mock_word_is_valid)
        monkeypatch.setattr(
            GameDictionary,
            "_add_word_to_words_by_first_letter",
            mock___add_word_to_words_by_first_letter,
        )
        monkeypatch.setattr(
            GameDictionary,
            "_add_word_to_words_by_uniques",
            mock__add_word_to_words_by_uniques,
        )

        gd = GameDictionary(tmp_file, "")
        gd.create()
        assert gd.valid_words == 4

    def test_create_from_file_white_space(self, monkeypatch, tmp_path):
        tmp_file = tmp_path / "test_dic.txt"
        tmp_file.write_text("apple\nbanant  \r\n  cherry\n\tdate\n")

        def mock_word_is_valid(_mSelf, _word):
            return True

        def mock___add_word_to_words_by_first_letter(mSelf, word):
            pass

        def mock__add_word_to_words_by_uniques(mSelf, word):
            pass

        monkeypatch.setattr(GameDictionary, "word_is_valid", mock_word_is_valid)
        monkeypatch.setattr(
            GameDictionary,
            "_add_word_to_words_by_first_letter",
            mock___add_word_to_words_by_first_letter,
        )
        monkeypatch.setattr(
            GameDictionary,
            "_add_word_to_words_by_uniques",
            mock__add_word_to_words_by_uniques,
        )

        gd = GameDictionary(tmp_file, "")
        gd.create()
        assert gd.valid_words == 4

    def test_create_from_file_all_bad(self, monkeypatch, tmp_path):
        tmp_file = tmp_path / "test_dic.txt"
        tmp_file.write_text("apple\nbanana\ncherry\ndate\n")

        def mock_word_is_valid(_mSelf, _word):
            return False

        monkeypatch.setattr(GameDictionary, "word_is_valid", mock_word_is_valid)

        gd = GameDictionary(tmp_file, "")
        gd.create()
        assert gd.invalid_words == 4

    def test_ordered_by_uniques(self):
        pass
