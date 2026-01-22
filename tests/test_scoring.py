import unittest

from src.services.dadata import CompanyProfile
from src.services.inn_validation import is_valid_inn
from src.services.scoring import score_company


class TestInnValidation(unittest.TestCase):
    def test_valid_inn(self):
        self.assertTrue(is_valid_inn("7707083893"))
        self.assertTrue(is_valid_inn("500100732259"))

    def test_invalid_inn(self):
        self.assertFalse(is_valid_inn(""))
        self.assertFalse(is_valid_inn("123"))
        self.assertFalse(is_valid_inn("abc123"))


class TestScoring(unittest.TestCase):
    def test_high_risk_for_inactive(self):
        profile = CompanyProfile(
            name="Test",
            inn="7707083893",
            ogrn="1027700132195",
            kpp="770701001",
            address="Москва",
            director="Иванов И.И.",
            status="LIQUIDATED",
            registration_date="2020-01-01",
            is_mass_address=None,
            is_mass_director=None,
        )
        score = score_company(profile)
        self.assertEqual(score.level, "HIGH")

    def test_medium_risk_for_missing_fields(self):
        profile = CompanyProfile(
            name=None,
            inn="7707083893",
            ogrn=None,
            kpp=None,
            address=None,
            director=None,
            status="ACTIVE",
            registration_date="2020-01-01",
            is_mass_address=None,
            is_mass_director=None,
        )
        score = score_company(profile)
        self.assertEqual(score.level, "MEDIUM")


if __name__ == "__main__":
    unittest.main()
