"""
Тесты для парсинга данных из DaData API (максимальный тариф)
"""
import unittest
from unittest.mock import patch, MagicMock

from src.integrations.dadata import DaDataClient


# Полный ответ DaData (максимальный тариф) для тестирования
FULL_SUGGESTION = {
    "value": 'ООО "РОМАШКА"',
    "unrestricted_value": 'Общество с ограниченной ответственностью "РОМАШКА"',
    "data": {
        "inn": "7707083893",
        "kpp": "770701001",
        "ogrn": "1027700132195",
        "ogrn_date": 1027715200000,
        "hid": "abc123hid",
        "type": "LEGAL",
        "name": {
            "full_with_opf": 'Общество с ограниченной ответственностью "РОМАШКА"',
            "short_with_opf": 'ООО "РОМАШКА"',
            "latin": "ROMASHKA LLC",
            "full": "РОМАШКА",
            "short": "РОМАШКА",
        },
        "opf": {
            "code": "12300",
            "full": "Общество с ограниченной ответственностью",
            "short": "ООО",
        },
        "state": {
            "status": "ACTIVE",
            "code": None,
            "actuality_date": 1700000000000,
            "registration_date": 1027715200000,
            "liquidation_date": None,
        },
        "address": {
            "value": "г Москва, ул Тверская, д 1",
            "unrestricted_value": "127000, г Москва, ул Тверская, д 1",
            "data": {
                "postal_code": "127000",
                "country": "Россия",
                "region_with_type": "г Москва",
                "geo_lat": "55.764",
                "geo_lon": "37.606",
            },
        },
        "branch_type": "MAIN",
        "branch_count": 3,
        "management": {
            "name": "Иванов Иван Иванович",
            "post": "Генеральный директор",
            "disqualified": None,
        },
        "okved": "62.01",
        "okved_type": "2014",
        "okveds": [
            {"main": True, "type": "2014", "code": "62.01", "name": "Разработка ПО"},
            {"main": False, "type": "2014", "code": "63.11", "name": "Обработка данных"},
        ],
        "okpo": "12345678",
        "okato": "45286560000",
        "oktmo": "45362000",
        "okogu": "4210014",
        "okfs": "16",
        "employee_count": 150,
        "capital": {"type": "Уставный капитал", "value": 100000},
        "founders": [
            {
                "ogrn": None,
                "inn": "770700001111",
                "name": "Петров Пётр Петрович",
                "fio": {"surname": "Петров", "name": "Пётр", "patronymic": "Петрович"},
                "hid": "founder1",
                "type": "PHYSICAL",
                "share": {"type": "PERCENT", "value": 60, "numerator": 60, "denominator": 100},
            },
            {
                "ogrn": "1027700000001",
                "inn": "7707000001",
                "name": 'ООО "ИНВЕСТ"',
                "fio": None,
                "hid": "founder2",
                "type": "LEGAL",
                "share": {"type": "PERCENT", "value": 40, "numerator": 40, "denominator": 100},
            },
        ],
        "managers": [
            {
                "inn": "770700002222",
                "fio": {"surname": "Иванов", "name": "Иван", "patronymic": "Иванович"},
                "post": "Генеральный директор",
                "name": "Иванов Иван Иванович",
                "hid": "manager1",
                "type": "EMPLOYEE",
            },
        ],
        "finance": {
            "tax_system": "OSN",
            "income": 50000000,
            "expense": 40000000,
            "revenue": 50000000,
            "debt": 100000,
            "penalty": 5000,
            "year": 2023,
        },
        "phones": [
            {"value": "+7 (495) 123-45-67"},
            {"value": "+7 (495) 765-43-21"},
        ],
        "emails": [
            {"value": "info@romashka.ru"},
        ],
        "licenses": [
            {
                "series": "77",
                "number": "Л041-00001",
                "issue_date": 1600000000000,
                "issue_authority": "Минздрав",
                "suspend_date": None,
                "suspend_authority": None,
                "valid_from": 1600000000000,
                "valid_to": None,
                "activities": ["Медицинская деятельность"],
                "addresses": ["г Москва, ул Тверская, д 1"],
            }
        ],
        "authorities": {
            "fts_registration": {
                "type": "FEDERAL_TAX_SERVICE",
                "code": "7746",
                "name": "ИФНС №46 по г. Москве",
                "address": "г Москва",
            },
            "fts_report": {
                "type": "FEDERAL_TAX_SERVICE",
                "code": "7707",
                "name": "ИФНС №7 по г. Москве",
                "address": "г Москва",
            },
            "pf": {
                "type": "PENSION_FUND",
                "code": "087101",
                "name": "ГУ ПФР №10",
                "address": None,
            },
            "sif": {
                "type": "SOCIAL_INSURANCE_FUND",
                "code": "7710",
                "name": "Филиал №10 ГУ МРО ФСС",
                "address": None,
            },
        },
        "documents": {
            "fts_registration": {
                "type": "FTS_REGISTRATION",
                "series": "77",
                "number": "001234567",
                "issue_date": 1027715200000,
                "issue_authority": "7746",
            },
        },
        "predecessors": [
            {"ogrn": "1020000000001", "inn": "5000000001", "name": 'ЗАО "СТАРАЯ РОМАШКА"'},
        ],
        "successors": [],
    },
}

MINIMAL_SUGGESTION = {
    "value": 'ИП Сидоров',
    "data": {
        "inn": "123456789012",
        "kpp": None,
        "ogrn": "300000000000001",
        "type": "INDIVIDUAL",
        "name": {
            "full_with_opf": "Индивидуальный предприниматель Сидоров Сидор Сидорович",
            "short_with_opf": "ИП Сидоров С.С.",
        },
        "state": {
            "status": "ACTIVE",
            "registration_date": 1600000000000,
        },
        "address": {"value": "г Казань"},
    },
}


class TestDaDataParser(unittest.TestCase):
    """Тесты парсинга полей DaData"""

    def setUp(self):
        with patch("src.integrations.dadata.settings") as mock_settings:
            mock_settings.dadata_api_key = "test_key"
            mock_settings.dadata_secret_key = "test_secret"
            self.client = DaDataClient.__new__(DaDataClient)
            self.client.api_key = "test_key"
            self.client.secret_key = "test_secret"
            self.client.headers = {}

    # --- Основные идентификаторы ---

    def test_parse_identifiers(self):
        """Парсинг основных идентификаторов: ИНН, КПП, ОГРН, ogrn_date, hid, type"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertEqual(result["inn"], "7707083893")
        self.assertEqual(result["kpp"], "770701001")
        self.assertEqual(result["ogrn"], "1027700132195")
        self.assertEqual(result["ogrn_date"], 1027715200000)
        self.assertEqual(result["hid"], "abc123hid")
        self.assertEqual(result["type"], "LEGAL")

    # --- Наименование ---

    def test_parse_name_all_fields(self):
        """Парсинг всех полей наименования"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        name = result["name"]
        self.assertEqual(name["full_with_opf"], 'Общество с ограниченной ответственностью "РОМАШКА"')
        self.assertEqual(name["short_with_opf"], 'ООО "РОМАШКА"')
        self.assertEqual(name["latin"], "ROMASHKA LLC")
        self.assertEqual(name["full"], "РОМАШКА")
        self.assertEqual(name["short"], "РОМАШКА")

    # --- ОПФ ---

    def test_parse_opf(self):
        """Парсинг ОПФ (организационно-правовая форма)"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        opf = result["opf"]
        self.assertEqual(opf["code"], "12300")
        self.assertEqual(opf["full"], "Общество с ограниченной ответственностью")
        self.assertEqual(opf["short"], "ООО")

    # --- Статус ---

    def test_parse_state(self):
        """Парсинг состояния с actuality_date и code"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        state = result["state"]
        self.assertEqual(state["status"], "ACTIVE")
        self.assertEqual(state["actuality_date"], 1700000000000)
        self.assertEqual(state["registration_date"], 1027715200000)
        self.assertIsNone(state["liquidation_date"])

    # --- Адрес ---

    def test_parse_address(self):
        """Парсинг адреса с unrestricted_value"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        addr = result["address"]
        self.assertEqual(addr["value"], "г Москва, ул Тверская, д 1")
        self.assertEqual(addr["unrestricted_value"], "127000, г Москва, ул Тверская, д 1")
        self.assertEqual(addr["data"]["postal_code"], "127000")

    # --- Филиалы ---

    def test_parse_branches(self):
        """Парсинг типа и количества филиалов"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertEqual(result["branch_type"], "MAIN")
        self.assertEqual(result["branch_count"], 3)

    # --- Классификаторы ---

    def test_parse_classifiers(self):
        """Парсинг ОКПО, ОКАТО, ОКТМО, ОКОГУ, ОКФС"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertEqual(result["okpo"], "12345678")
        self.assertEqual(result["okato"], "45286560000")
        self.assertEqual(result["oktmo"], "45362000")
        self.assertEqual(result["okogu"], "4210014")
        self.assertEqual(result["okfs"], "16")

    # --- ОКВЭД ---

    def test_parse_okveds(self):
        """Парсинг основного и дополнительных ОКВЭД"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertEqual(result["okved"], "62.01")
        self.assertEqual(result["okved_type"], "2014")
        self.assertIsNotNone(result["okveds"])
        self.assertEqual(len(result["okveds"]), 2)
        self.assertEqual(result["okveds"][0]["code"], "62.01")
        self.assertTrue(result["okveds"][0]["main"])

    # --- Уставный капитал ---

    def test_parse_capital(self):
        """Парсинг уставного капитала"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("capital", result)
        self.assertEqual(result["capital"]["type"], "Уставный капитал")
        self.assertEqual(result["capital"]["value"], 100000)

    # --- Учредители ---

    def test_parse_founders(self):
        """Парсинг учредителей"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("founders", result)
        self.assertEqual(len(result["founders"]), 2)

        physical = result["founders"][0]
        self.assertEqual(physical["type"], "PHYSICAL")
        self.assertEqual(physical["inn"], "770700001111")
        self.assertEqual(physical["share"]["type"], "PERCENT")
        self.assertEqual(physical["share"]["value"], 60)

        legal = result["founders"][1]
        self.assertEqual(legal["type"], "LEGAL")
        self.assertEqual(legal["name"], 'ООО "ИНВЕСТ"')

    # --- Руководители (managers) ---

    def test_parse_managers(self):
        """Парсинг руководителей"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("managers", result)
        self.assertEqual(len(result["managers"]), 1)
        m = result["managers"][0]
        self.assertEqual(m["post"], "Генеральный директор")
        self.assertEqual(m["fio"]["surname"], "Иванов")

    # --- Финансы (расширенные) ---

    def test_parse_finance_extended(self):
        """Парсинг расширенных финансовых данных: tax_system, income, debt, penalty"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("finance", result)
        fin = result["finance"]
        self.assertEqual(fin["tax_system"], "OSN")
        self.assertEqual(fin["income"], 50000000)
        self.assertEqual(fin["expense"], 40000000)
        self.assertEqual(fin["revenue"], 50000000)
        self.assertEqual(fin["debt"], 100000)
        self.assertEqual(fin["penalty"], 5000)
        self.assertEqual(fin["year"], 2023)

    # --- Контакты ---

    def test_parse_phones(self):
        """Парсинг телефонов"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("phones", result)
        self.assertEqual(len(result["phones"]), 2)
        self.assertEqual(result["phones"][0], "+7 (495) 123-45-67")

    def test_parse_emails(self):
        """Парсинг email"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("emails", result)
        self.assertEqual(result["emails"], ["info@romashka.ru"])

    # --- Лицензии ---

    def test_parse_licenses(self):
        """Парсинг лицензий"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("licenses", result)
        self.assertEqual(len(result["licenses"]), 1)
        lic = result["licenses"][0]
        self.assertEqual(lic["number"], "Л041-00001")
        self.assertEqual(lic["activities"], ["Медицинская деятельность"])

    # --- Регистрирующие органы ---

    def test_parse_authorities(self):
        """Парсинг регистрирующих органов"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("authorities", result)
        fts = result["authorities"]["fts_registration"]
        self.assertEqual(fts["code"], "7746")
        self.assertIn("pf", result["authorities"])
        self.assertIn("sif", result["authorities"])

    # --- Документы ---

    def test_parse_documents(self):
        """Парсинг документов"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("documents", result)
        self.assertIn("fts_registration", result["documents"])

    # --- Правопредшественники ---

    def test_parse_predecessors(self):
        """Парсинг правопредшественников"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertIn("predecessors", result)
        self.assertEqual(len(result["predecessors"]), 1)
        self.assertEqual(result["predecessors"][0]["inn"], "5000000001")

    # --- Правопреемники (пустой массив не добавляется) ---

    def test_no_successors_when_empty(self):
        """Пустой массив правопреемников не добавляется в результат"""
        result = self.client._parse_company_data(FULL_SUGGESTION)
        self.assertNotIn("successors", result)

    # --- Минимальные данные (ИП) ---

    def test_parse_minimal_suggestion(self):
        """Парсинг минимального набора данных (ИП без финансов)"""
        result = self.client._parse_company_data(MINIMAL_SUGGESTION)
        self.assertEqual(result["inn"], "123456789012")
        self.assertIsNone(result["kpp"])
        self.assertEqual(result["type"], "INDIVIDUAL")
        self.assertNotIn("finance", result)
        self.assertNotIn("founders", result)
        self.assertNotIn("phones", result)
        self.assertNotIn("licenses", result)

    # --- Отсутствие необязательных полей ---

    def test_missing_optional_fields(self):
        """Если опциональных полей нет в data, они не добавляются в результат"""
        result = self.client._parse_company_data(MINIMAL_SUGGESTION)
        self.assertNotIn("capital", result)
        self.assertNotIn("managers", result)
        self.assertNotIn("emails", result)
        self.assertNotIn("authorities", result)
        self.assertNotIn("documents", result)
        self.assertNotIn("predecessors", result)
        self.assertNotIn("successors", result)


class TestTelegramFormat(unittest.TestCase):
    """Тесты форматирования ответа для Telegram"""

    def test_format_response_full(self):
        """Формат ответа содержит все основные поля"""
        from src.handlers.telegram_handler import _format_response

        with patch("src.integrations.dadata.settings"), \
             patch("src.integrations.openai_client.settings"):
            client = DaDataClient.__new__(DaDataClient)
            client.api_key = "test"
            client.secret_key = "test"
            client.headers = {}

            company_data = client._parse_company_data(FULL_SUGGESTION)
            result = _format_response(company_data, "GPT анализ")

            # Основные реквизиты
            self.assertIn("7707083893", result)
            self.assertIn("770701001", result)
            self.assertIn("1027700132195", result)
            # Название
            self.assertIn("РОМАШКА", result)
            # Статус
            self.assertIn("ACTIVE", result)
            # Капитал
            self.assertIn("100000", result)
            # Финансы
            self.assertIn("ФИНАНСЫ", result)
            self.assertIn("OSN", result)
            # Учредители
            self.assertIn("УЧРЕДИТЕЛИ", result)
            self.assertIn("Петров", result)
            # Руководители
            self.assertIn("РУКОВОДИТЕЛИ", result)
            # Лицензии
            self.assertIn("ЛИЦЕНЗИИ", result)
            # Контакты
            self.assertIn("+7 (495) 123-45-67", result)
            self.assertIn("info@romashka.ru", result)
            # Классификаторы
            self.assertIn("ОКПО", result)
            # GPT analysis
            self.assertIn("GPT анализ", result)


class TestBitrixFormat(unittest.TestCase):
    """Тесты форматирования ответа для Bitrix24"""

    def test_format_bitrix_response_full(self):
        """Формат ответа Bitrix содержит все основные поля"""
        from src.handlers.bitrix_handler import _format_bitrix_response

        with patch("src.integrations.dadata.settings"), \
             patch("src.integrations.openai_client.settings"):
            client = DaDataClient.__new__(DaDataClient)
            client.api_key = "test"
            client.secret_key = "test"
            client.headers = {}

            company_data = client._parse_company_data(FULL_SUGGESTION)
            result = _format_bitrix_response(company_data, "GPT анализ")

            self.assertIn("7707083893", result)
            self.assertIn("ACTIVE", result)
            self.assertIn("100000", result)
            self.assertIn("УЧРЕДИТЕЛИ", result)
            self.assertIn("РУКОВОДИТЕЛИ", result)
            self.assertIn("ЛИЦЕНЗИИ", result)
            self.assertIn("GPT анализ", result)


if __name__ == "__main__":
    unittest.main()
