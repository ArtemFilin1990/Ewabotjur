import unittest

from src.services.dadata import CompanyInfo
from src.services.scoring import score_company, validate_inn


class TestScoring(unittest.TestCase):
    def test_validate_inn(self):
        self.assertTrue(validate_inn("7707083893"))
        self.assertTrue(validate_inn("500100732259"))
        self.assertFalse(validate_inn("123"))
        self.assertFalse(validate_inn("77A083893"))

    def test_score_company_high_risk(self):
        company = CompanyInfo(
            inn="7707083893",
            name="Test",
            ogrn="1027700132195",
            kpp="773601001",
            address="Москва",
            director="Иванов",
            status="LIQUIDATING",
            registration_date="2010-01-01",
            mass_address=None,
            mass_director=None,
        )
        result = score_company(company)
        self.assertEqual(result.level, "HIGH")

    def test_score_company_medium_risk_missing_fields(self):
        company = CompanyInfo(
            inn="7707083893",
            name="Test",
            ogrn=None,
            kpp=None,
            address=None,
            director=None,
            status="ACTIVE",
            registration_date=None,
            mass_address=None,
            mass_director=None,
        )
        result = score_company(company)
        self.assertEqual(result.level, "MEDIUM")


if __name__ == "__main__":
    unittest.main()
