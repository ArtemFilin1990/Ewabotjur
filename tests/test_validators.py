import unittest

from src.services.validators import validate_inn


class TestValidateInn(unittest.TestCase):
    def test_valid_inn_10_digits(self):
        self.assertTrue(validate_inn("7707083893"))

    def test_valid_inn_12_digits(self):
        self.assertTrue(validate_inn("770708389301"))

    def test_invalid_inn_length(self):
        self.assertFalse(validate_inn("123"))

    def test_invalid_inn_non_digits(self):
        self.assertFalse(validate_inn("77A083893"))


if __name__ == "__main__":
    unittest.main()
