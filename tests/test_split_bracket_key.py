"""
Тесты для парсера Bitrix form data ключей
"""
import unittest
from src.main import _split_bracket_key


class TestSplitBracketKey(unittest.TestCase):
    """Тесты _split_bracket_key"""

    def test_plain_key(self):
        self.assertEqual(_split_bracket_key("event"), ["event"])

    def test_single_bracket(self):
        self.assertEqual(_split_bracket_key("data[USER]"), ["data", "USER"])

    def test_nested_brackets(self):
        self.assertEqual(
            _split_bracket_key("data[PARAMS][MESSAGE]"),
            ["data", "PARAMS", "MESSAGE"],
        )

    def test_deep_nesting(self):
        self.assertEqual(
            _split_bracket_key("a[b][c][d]"),
            ["a", "b", "c", "d"],
        )

    def test_empty_brackets_ignored(self):
        # Empty bracket content is not a valid part
        self.assertEqual(_split_bracket_key("a[]b"), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
