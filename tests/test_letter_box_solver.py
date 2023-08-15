import lbsolve.letter_boxed_solver as lbs


class TestArgs:
    def test_split_letter_group(self):
        group = "abcd"
        letters = lbs.split_letter_group(group)
        assert letters == ["a", "b", "c", "d"]
