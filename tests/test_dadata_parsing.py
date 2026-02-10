"""
Тесты расширенного парсинга данных DaData.
"""
import unittest

from src.integrations.dadata import DaDataClient


class TestDaDataParsing(unittest.TestCase):
    """Проверка парсинга полей максимального тарифа DaData."""

    def setUp(self) -> None:
        self.client = DaDataClient()

    def _parse(self, extra_data):
        base_data = {
            "inn": "7707083893",
            "kpp": "773601001",
            "ogrn": "1027700132195",
            "name": {
                "full": "ПАО СБЕРБАНК",
                "short": "СБЕРБАНК",
                "latin": "SBERBANK",
                "full_with_opf": "ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО СБЕРБАНК",
                "short_with_opf": "ПАО СБЕРБАНК",
            },
            "address": {
                "value": "г Москва, ул Вавилова, д 19",
                "unrestricted_value": "119333, г Москва, ул Вавилова, д 19",
                "data": {},
            },
            "state": {
                "status": "ACTIVE",
                "registration_date": "2001-01-01",
                "liquidation_date": None,
                "actuality_date": "2024-01-01",
                "code": "ACTIVE",
            },
        }
        data = {**base_data, **extra_data}
        return self.client._parse_company_data({"data": data})

    def test_parses_ogrn_date(self):
        parsed = self._parse({"ogrn_date": "2001-02-03"})
        self.assertEqual(parsed["ogrn_date"], "2001-02-03")

    def test_parses_hid(self):
        parsed = self._parse({"hid": "1234567890123"})
        self.assertEqual(parsed["hid"], "1234567890123")

    def test_parses_name_variants(self):
        parsed = self._parse({})
        self.assertEqual(parsed["name"]["full"], "ПАО СБЕРБАНК")
        self.assertEqual(parsed["name"]["short"], "СБЕРБАНК")
        self.assertEqual(parsed["name"]["latin"], "SBERBANK")

    def test_parses_opf_fields(self):
        parsed = self._parse({"opf": {"code": "123", "full": "Полное", "short": "Краткое"}})
        self.assertEqual(parsed["opf"]["code"], "123")
        self.assertEqual(parsed["opf"]["full"], "Полное")
        self.assertEqual(parsed["opf"]["short"], "Краткое")

    def test_parses_state_actuality_date_and_code(self):
        parsed = self._parse({"state": {"status": "ACTIVE", "actuality_date": "2023-12-12", "code": "ACTIVE"}})
        self.assertEqual(parsed["state"]["actuality_date"], "2023-12-12")
        self.assertEqual(parsed["state"]["code"], "ACTIVE")

    def test_parses_address_unrestricted_value(self):
        parsed = self._parse({"address": {"value": "адрес", "unrestricted_value": "полный адрес", "data": {}}})
        self.assertEqual(parsed["address"]["unrestricted_value"], "полный адрес")

    def test_parses_branch_fields(self):
        parsed = self._parse({"branch_type": "MAIN", "branch_count": 2})
        self.assertEqual(parsed["branch_type"], "MAIN")
        self.assertEqual(parsed["branch_count"], 2)

    def test_parses_okpo_okato_oktmo_okogu_okfs(self):
        parsed = self._parse(
            {
                "okpo": "12345678",
                "okato": "45286565000",
                "oktmo": "45383000000",
                "okogu": "4210014",
                "okfs": "16",
            }
        )
        self.assertEqual(parsed["okpo"], "12345678")
        self.assertEqual(parsed["okato"], "45286565000")
        self.assertEqual(parsed["oktmo"], "45383000000")
        self.assertEqual(parsed["okogu"], "4210014")
        self.assertEqual(parsed["okfs"], "16")

    def test_parses_okved_type(self):
        parsed = self._parse({"okved_type": "2014"})
        self.assertEqual(parsed["okved_type"], "2014")

    def test_parses_okveds_list(self):
        okveds = [{"code": "64.19", "name": "Денежное посредничество"}]
        parsed = self._parse({"okveds": okveds})
        self.assertEqual(parsed["okveds"], okveds)

    def test_parses_capital(self):
        capital = {"type": "зарегистрированный", "value": 1000000}
        parsed = self._parse({"capital": capital})
        self.assertEqual(parsed["capital"], capital)

    def test_parses_founders(self):
        founders = [{"name": "Иванов Иван"}]
        parsed = self._parse({"founders": founders})
        self.assertEqual(parsed["founders"], founders)

    def test_parses_managers(self):
        managers = [{"name": "Петров Петр"}]
        parsed = self._parse({"managers": managers})
        self.assertEqual(parsed["managers"], managers)

    def test_parses_finance_extended(self):
        finance = {"tax_system": "OSNO", "income": 1000, "debt": 200, "penalty": 10}
        parsed = self._parse({"finance": finance})
        self.assertEqual(parsed["finance"]["tax_system"], "OSNO")
        self.assertEqual(parsed["finance"]["income"], 1000)
        self.assertEqual(parsed["finance"]["debt"], 200)
        self.assertEqual(parsed["finance"]["penalty"], 10)

    def test_parses_phones(self):
        phones = ["+7 495 000-00-00"]
        parsed = self._parse({"phones": phones})
        self.assertEqual(parsed["phones"], phones)

    def test_parses_emails(self):
        emails = ["info@example.com"]
        parsed = self._parse({"emails": emails})
        self.assertEqual(parsed["emails"], emails)

    def test_parses_licenses(self):
        licenses = [{"number": "123", "issue_date": "2020-01-01"}]
        parsed = self._parse({"licenses": licenses})
        self.assertEqual(parsed["licenses"], licenses)

    def test_parses_authorities(self):
        authorities = [{"type": "ФНС"}]
        parsed = self._parse({"authorities": authorities})
        self.assertEqual(parsed["authorities"], authorities)

    def test_parses_documents(self):
        documents = [{"type": "Устав"}]
        parsed = self._parse({"documents": documents})
        self.assertEqual(parsed["documents"], documents)

    def test_parses_predecessors(self):
        predecessors = [{"inn": "1234567890"}]
        parsed = self._parse({"predecessors": predecessors})
        self.assertEqual(parsed["predecessors"], predecessors)

    def test_parses_successors(self):
        successors = [{"inn": "0987654321"}]
        parsed = self._parse({"successors": successors})
        self.assertEqual(parsed["successors"], successors)

    def test_parses_citizenship(self):
        parsed = self._parse({"citizenship": "RU"})
        self.assertEqual(parsed["citizenship"], "RU")

    def test_parses_fio(self):
        fio = {"surname": "Иванов", "name": "Иван", "patronymic": "Иванович"}
        parsed = self._parse({"fio": fio})
        self.assertEqual(parsed["fio"], fio)


if __name__ == "__main__":
    unittest.main()
