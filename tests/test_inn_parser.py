"""
Тесты для парсера ИНН
"""
import unittest
from src.utils.inn_parser import extract_inn, extract_all_inns, validate_inn


class TestINNParser(unittest.TestCase):
    """Тесты парсера ИНН"""
    
    def test_extract_inn_10_digits(self):
        """Тест извлечения 10-значного ИНН"""
        text = "Проверьте компанию с ИНН 7707083893"
        inn = extract_inn(text)
        self.assertEqual(inn, "7707083893")
    
    def test_extract_inn_12_digits(self):
        """Тест извлечения 12-значного ИНН"""
        text = "ИП с ИНН 123456789012"
        inn = extract_inn(text)
        self.assertEqual(inn, "123456789012")
    
    def test_extract_inn_no_match(self):
        """Тест когда ИНН нет в тексте"""
        text = "Привет, как дела?"
        inn = extract_inn(text)
        self.assertIsNone(inn)
    
    def test_extract_inn_only_digits(self):
        """Тест извлечения ИНН из текста только с цифрами"""
        text = "7707083893"
        inn = extract_inn(text)
        self.assertEqual(inn, "7707083893")
    
    def test_extract_all_inns(self):
        """Тест извлечения всех ИНН из текста"""
        text = "Первая компания 7707083893, вторая 1234567890"
        inns = extract_all_inns(text)
        self.assertEqual(len(inns), 2)
        self.assertIn("7707083893", inns)
        self.assertIn("1234567890", inns)
    
    def test_validate_inn_valid_10(self):
        """Тест валидации корректного 10-значного ИНН"""
        # Известный валидный ИНН (Яндекс)
        self.assertTrue(validate_inn("7707083893"))
    
    def test_validate_inn_invalid_length(self):
        """Тест валидации ИНН неверной длины"""
        self.assertFalse(validate_inn("123"))
        self.assertFalse(validate_inn("12345678901234"))
    
    def test_validate_inn_non_digits(self):
        """Тест валидации ИНН с нецифровыми символами"""
        self.assertFalse(validate_inn("770708389A"))
    
    def test_validate_inn_invalid_checksum(self):
        """Тест валидации ИНН с неверной контрольной суммой"""
        # Изменяем последнюю цифру валидного ИНН
        self.assertFalse(validate_inn("7707083892"))


if __name__ == "__main__":
    unittest.main()
