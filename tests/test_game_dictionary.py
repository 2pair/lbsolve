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

    def test_add_to_node_none(self):
        node = {}
        GameDictionary._add_to_node(node, list())
        assert node == {None: None}

    def test_add_to_node_one(self):
        node = {}
        GameDictionary._add_to_node(node, ["g"])
        assert node == {"g": {None: None}}

    def test_add_to_node_recursive(self):
        node = {}
        GameDictionary._add_to_node(node, ["g", "o"])
        assert node == {"g": {"o": {None: None}}}

    def test_add_to_trie_one(self):
        trie = {}
        gd = GameDictionary("", "")
        gd._add_to_trie(trie, "cat")
        assert trie == {
            "c": {
                "a": {
                    "t": {None: {"unique_letters": {"c", "a", "t"}, "num_uniques": 3}}
                }
            }
        }

    def test_add_to_trie_multi(self):
        trie = {}
        gd = GameDictionary("", "")
        gd._add_to_trie(trie, "cat")
        gd._add_to_trie(trie, "car")
        gd._add_to_trie(trie, "cart")
        gd._add_to_trie(trie, "call")

        assert trie == {
            "c": {
                "a": {
                    "t": {None: {"unique_letters": {"c", "a", "t"}, "num_uniques": 3}},
                    "r": {
                        None: {"unique_letters": {"c", "a", "r"}, "num_uniques": 3},
                        "t": {
                            None: {
                                "unique_letters": {"c", "a", "r", "t"},
                                "num_uniques": 4,
                            }
                        },
                    },
                    "l": {
                        "l": {
                            None: {"unique_letters": {"c", "a", "l"}, "num_uniques": 3}
                        }
                    },
                }
            }
        }


# TODO test add from file, class creation
