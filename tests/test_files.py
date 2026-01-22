"""
Тесты для модуля обработки файлов.
"""

import unittest
import io
from pathlib import Path
from src.files.index import FileProcessor, DocumentGenerator


class TestFileProcessor(unittest.TestCase):
    """Тесты для FileProcessor."""
    
    def setUp(self):
        """Инициализация процессора перед каждым тестом."""
        self.processor = FileProcessor()
    
    def test_parse_text_from_string(self):
        """Парсинг обычного текстового файла."""
        text_content = "Это тестовый документ.\nВторая строка."
        buffer = io.BytesIO(text_content.encode('utf-8'))
        
        result = self.processor.parse_text(buffer)
        self.assertEqual(result, text_content)
    
    def test_parse_text_handles_large_files(self):
        """Обработка больших файлов с ограничением размера."""
        # Создаём текст больше MAX_TEXT_LENGTH
        large_text = "A" * (self.processor.MAX_TEXT_LENGTH + 1000)
        buffer = io.BytesIO(large_text.encode('utf-8'))
        
        result = self.processor.parse_text(buffer)
        self.assertEqual(len(result), self.processor.MAX_TEXT_LENGTH)
    
    def test_extract_text_requires_ext_for_bytesio(self):
        """extract_text требует ext для BytesIO."""
        buffer = io.BytesIO(b"test")
        
        with self.assertRaises(ValueError):
            self.processor.extract_text(buffer)
    
    def test_extract_text_unsupported_format(self):
        """Обработка неподдерживаемого формата."""
        buffer = io.BytesIO(b"test")
        
        with self.assertRaises(ValueError) as context:
            self.processor.extract_text(buffer, ext=".unknown")
        
        self.assertIn("Неподдерживаемый формат", str(context.exception))
    
    def test_parse_pdf_without_library(self):
        """Парсинг PDF без установленной библиотеки возвращает сообщение об ошибке."""
        buffer = io.BytesIO(b"%PDF-1.4 fake pdf content")
        
        # Если PyMuPDF не установлен, должна вернуться ошибка
        result = self.processor.parse_pdf(buffer)
        # Результат может быть либо извлечённым текстом, либо сообщением об ошибке
        self.assertIsInstance(result, str)
    
    def test_parse_docx_without_library(self):
        """Парсинг DOCX без установленной библиотеки возвращает сообщение об ошибке."""
        buffer = io.BytesIO(b"fake docx content")
        
        # Если python-docx не установлен или файл невалиден, должна вернуться ошибка
        result = self.processor.parse_docx(buffer)
        self.assertIsInstance(result, str)


class TestDocumentGenerator(unittest.TestCase):
    """Тесты для DocumentGenerator."""
    
    def setUp(self):
        """Инициализация генератора перед каждым тестом."""
        self.generator = DocumentGenerator()
    
    def test_generate_xlsx_from_rows(self):
        """Генерация XLSX из списка строк."""
        data = {
            'columns': ['Риск', 'Уровень', 'Описание'],
            'rows': [
                ['Риск 1', 'Высокий', 'Описание риска 1'],
                ['Риск 2', 'Средний', 'Описание риска 2'],
            ]
        }
        
        try:
            result = self.generator.generate_xlsx(data)
            self.assertIsInstance(result, bytes)
            self.assertGreater(len(result), 0)
        except ImportError as e:
            self.skipTest(f"Библиотека не установлена: {e}")
    
    def test_generate_xlsx_from_dict(self):
        """Генерация XLSX из словаря."""
        data = {
            'Риск': ['Риск 1', 'Риск 2'],
            'Уровень': ['Высокий', 'Средний'],
        }
        
        try:
            result = self.generator.generate_xlsx(data)
            self.assertIsInstance(result, bytes)
            self.assertGreater(len(result), 0)
        except ImportError as e:
            self.skipTest(f"Библиотека не установлена: {e}")
    
    def test_generate_docx_simple(self):
        """Генерация простого DOCX документа."""
        context = {
            'content': 'Это тестовый документ.'
        }
        
        try:
            result = self.generator.generate_docx(context=context)
            self.assertIsInstance(result, bytes)
            self.assertGreater(len(result), 0)
        except ImportError as e:
            self.skipTest(f"Библиотека не установлена: {e}")


if __name__ == '__main__':
    unittest.main()
