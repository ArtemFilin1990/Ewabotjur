"""
Тесты для модуля промптов.
"""

import unittest
from src.prompts.index import PromptLoader, PromptType


class TestPromptLoader(unittest.TestCase):
    """Тесты для PromptLoader."""
    
    def setUp(self):
        """Инициализация загрузчика перед каждым тестом."""
        self.loader = PromptLoader()
    
    def test_load_prompt_returns_string(self):
        """Загрузка промпта возвращает строку."""
        prompt = self.loader.load_prompt(PromptType.RISK_TABLE)
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
    
    def test_load_prompt_caching(self):
        """Промпты кэшируются после первой загрузки."""
        prompt1 = self.loader.load_prompt(PromptType.RISK_TABLE)
        prompt2 = self.loader.load_prompt(PromptType.RISK_TABLE)
        
        # Должны быть одинаковыми (из кэша)
        self.assertEqual(prompt1, prompt2)
    
    def test_render_prompt_with_context(self):
        """Рендеринг промпта с контекстом."""
        context = {
            'user_input': 'Проанализируй договор',
            'extracted_text': 'ДОГОВОР ПОСТАВКИ №1...',
            'my_company': {
                'inn': '1234567890',
                'name': 'ООО "Тест"'
            }
        }
        
        rendered = self.loader.render_prompt(PromptType.RISK_TABLE, context)
        
        # Проверяем, что контекст подставился
        self.assertIn('Проанализируй договор', rendered)
        self.assertIn('ДОГОВОР ПОСТАВКИ', rendered)
        self.assertIn('1234567890', rendered)
    
    def test_render_prompt_handles_missing_context(self):
        """Рендеринг работает даже без контекста."""
        rendered = self.loader.render_prompt(PromptType.RISK_TABLE, {})
        
        # Должен вернуть промпт, но без подставленных данных
        self.assertIsInstance(rendered, str)
        self.assertGreater(len(rendered), 0)
    
    def test_get_all_prompts(self):
        """Получение всех промптов."""
        all_prompts = self.loader.get_all_prompts()
        
        self.assertIsInstance(all_prompts, dict)
        self.assertEqual(len(all_prompts), len(PromptType))
        
        # Все значения должны быть строками
        for prompt_type, prompt_text in all_prompts.items():
            self.assertIsInstance(prompt_type, PromptType)
            self.assertIsInstance(prompt_text, str)
            self.assertGreater(len(prompt_text), 0)
    
    def test_render_with_long_extracted_text(self):
        """Рендеринг с длинным текстом документа."""
        context = {
            'extracted_text': 'A' * 20000,  # Очень длинный текст
        }
        
        rendered = self.loader.render_prompt(PromptType.CONTRACT_AGENT_RF, context)
        
        # Промпт должен обрезать текст (в шаблоне используется [:15000])
        self.assertIn('A', rendered)
        # Полный текст не должен попасть в промпт
        self.assertLess(len(rendered), 25000)
    
    def test_jinja2_template_syntax(self):
        """Jinja2 синтаксис работает корректно."""
        context = {
            'my_company': {
                'inn': '1234567890',
                'name': 'ООО "Компания"',
                'address': 'Москва'
            }
        }
        
        rendered = self.loader.render_prompt(PromptType.CLAIM_RESPONSE, context)
        
        # Проверяем, что данные из словаря правильно извлечены
        self.assertIn('1234567890', rendered)
        self.assertIn('ООО "Компания"', rendered)


if __name__ == '__main__':
    unittest.main()
