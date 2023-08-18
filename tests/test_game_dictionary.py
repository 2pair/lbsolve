from pathlib import Path
from pytest_mock import mocker, MockerFixture

from lbsolve.game_dictionary import GameDictionary, Word, WordSequence


class TestWord:
    def test_init(self):
        word = Word("booboo")
        assert word._word == "booboo"
        assert word.first_letter == "b"
        assert word.last_letter == "o"
        assert word.unique_letters == {"b", "o"}

    def test_to_str(self):
        raw_word = "pleasant"
        word = Word(raw_word)
        assert str(word) == raw_word

    def test_to_repr(self):
        raw_word = "ferocious"
        word = Word(raw_word)
        assert repr(word) == f"Word({raw_word})"


class TestWordSequence:
    def test_init(self):
        word_sequence = WordSequence("big", "dirty", "stinking", "bass")
        assert word_sequence._word_sequence == ("big", "dirty", "stinking", "bass")

    def test_len(self):
        word_sequence = WordSequence("regrets", "look", "like", "texts")
        assert len(word_sequence) == 4

    def test_get_item(self):
        word_sequence = WordSequence("neighbors", "that", "should", "be", "friends")
        assert word_sequence[0] == "neighbors"
        assert word_sequence[-1] == "friends"
        assert word_sequence[1:3] == ("that", "should")

    
    def test_iter(self):
        words = ["let", "mom", "sleep"]
        word_sequence = WordSequence(*words)
        for index, word in enumerate(word_sequence):
            assert str(word) == words[index]

    def test_in(self):
        words = ["no", "sleep", "remix"]
        word_sequence = WordSequence(*words)
        for word in words:
            assert word in word_sequence


class TestGameDictionary:
    def test_get_letter_candidates_all(self):
        letter_groups = [["a", "b", "c"], ["d", "e", "f"]]
        gd = GameDictionary("", letter_groups)
        candidates = gd.get_letter_candidates()
        assert candidates == ["a", "b", "c", "d", "e", "f"]

    def test_get_letter_candidates_other_sides(self):
        letter_groups = [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]]
        gd = GameDictionary("", letter_groups)
        candidates = gd.get_letter_candidates("g")
        assert candidates == ["a", "b", "c", "d", "e", "f"]
        candidates = gd.get_letter_candidates("a")
        assert candidates == ["d", "e", "f", "g", "h", "i"]

    def test_word_is_valid_invalid_letters(self):
        letter_groups = [
            ["a", "b", "c"],
            ["d", "e", "f"],
            ["g", "h", "i"],
            ["j", "k", "l"],
        ]
        gd = GameDictionary("", letter_groups)
        assert gd.word_is_valid("pat") == False
        assert gd.word_is_valid("sat") == False
        assert gd.word_is_valid("rat") == False

    def test_word_is_valid_colocated_letters(self):
        letter_groups = [
            ["a", "b", "c"],
            ["d", "e", "f"],
            ["g", "h", "i"],
            ["j", "k", "l"],
        ]
        gd = GameDictionary("", letter_groups)
        assert gd.word_is_valid("bat") == False
        assert gd.word_is_valid("hide") == False
        assert gd.word_is_valid("lack") == False

    def test_word_is_valid_true(self):
        letter_groups = [
            ["a", "b", "c"],
            ["d", "e", "f"],
            ["g", "h", "i"],
            ["j", "k", "l"],
        ]
        gd = GameDictionary("", letter_groups)
        assert gd.word_is_valid("beg") == True
        assert gd.word_is_valid("head") == True
        assert gd.word_is_valid("lead") == True

    def test_create_from_file_all_good(self, monkeypatch, mocker: MockerFixture):
        def mock_open_ctx(*args, **kwargs):
            return ["apple\n", "banana\n", "cherry\n", "date"]
        
        def mock_word_is_valid(_word):
            return True
        
        def mock___add_word_to_words_by_first_letter(word):
            pass

        def mock__add_word_to_words_by_uniques(word):
            pass

        #mock_open.return_value = ["apple\n", "banana\n", "cherry\n", "date"]
        #mocked_open = mocker.mock_open(read_data="apple\nbanana\ncherry\ndate")
        mock_open = mocker.patch("pathlib:Path.open")
        mock_open().__enter__().return_value = ["apple\n", "banana\n", "cherry\n", "date"]
        monkeypatch.setattr(GameDictionary, "word_is_valid", mock_word_is_valid)
        monkeypatch.setattr(GameDictionary, "_add_word_to_words_by_first_letter", mock___add_word_to_words_by_first_letter)
        monkeypatch.setattr(GameDictionary, "_add_word_to_words_by_uniques", mock__add_word_to_words_by_uniques)

        gd = GameDictionary(Path("./fake_file"), "")
        gd.create()
        assert gd.valid_words == 4