import unittest
from datetime import datetime, timedelta, timezone

from src.services.dadata_service import CompanyCard
from src.services.scoring_service import RiskScoringService


class TestRiskScoringService(unittest.TestCase):
    def setUp(self):
        self.service = RiskScoringService()

    def test_high_risk_for_inactive_status(self):
        company = CompanyCard(
            name="Test",
            inn="1234567890",
            ogrn="123",
            kpp="456",
            address="Address",
            director="Director",
            status="LIQUIDATED",
            registration_date=datetime.now(tz=timezone.utc) - timedelta(days=365),
            raw_flags={},
        )
        assessment = self.service.evaluate(company)
        self.assertEqual(assessment.level, RiskScoringService.HIGH)

    def test_medium_risk_for_missing_fields(self):
        company = CompanyCard(
            name="Test",
            inn="1234567890",
            ogrn=None,
            kpp=None,
            address=None,
            director=None,
            status="ACTIVE",
            registration_date=datetime.now(tz=timezone.utc) - timedelta(days=365),
            raw_flags={},
        )
        assessment = self.service.evaluate(company)
        self.assertEqual(assessment.level, RiskScoringService.MEDIUM)


if __name__ == "__main__":
    unittest.main()
