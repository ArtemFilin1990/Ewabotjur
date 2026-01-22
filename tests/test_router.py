"""
Тесты для модуля маршрутизации.
"""

import unittest
from src.router.index import Router, Scenario


class TestRouter(unittest.TestCase):
    """Тесты для Router."""
    
    def setUp(self):
        """Инициализация роутера перед каждым тестом."""
        self.router = Router()
    
    def test_hard_gate_risk_table(self):
        """Hard gate для таблицы рисков."""
        scenario, confidence = self.router.route("создай таблицу рисков по договору")
        self.assertEqual(scenario, Scenario.RISK_TABLE)
        self.assertGreater(confidence, 0.9)
    
    def test_hard_gate_claim_response(self):
        """Hard gate для ответа на претензию."""
        scenario, confidence = self.router.route("нужно подготовить ответ на претензию")
        self.assertEqual(scenario, Scenario.CLAIM_RESPONSE)
        self.assertGreater(confidence, 0.9)
    
    def test_hard_gate_contract(self):
        """Hard gate для договора."""
        scenario, confidence = self.router.route("проверь договор поставки")
        self.assertEqual(scenario, Scenario.CONTRACT_AGENT_RF)
        self.assertGreater(confidence, 0.9)
    
    def test_hard_gate_dadata(self):
        """Hard gate для DaData запроса."""
        scenario, confidence = self.router.route("проверь ИНН 1234567890")
        self.assertEqual(scenario, Scenario.DADATA_CARD)
        self.assertGreater(confidence, 0.9)
    
    def test_soft_matching_with_keywords(self):
        """Soft matching на основе ключевых слов."""
        scenario, confidence = self.router.route("какие риски в этом договоре?")
        # Должно попасть либо в RISK_TABLE, либо в CONTRACT_AGENT_RF
        self.assertIn(scenario, [Scenario.RISK_TABLE, Scenario.CONTRACT_AGENT_RF])
        self.assertGreater(confidence, 0.0)
    
    def test_low_confidence_empty_text(self):
        """Низкая уверенность для пустого текста."""
        scenario, confidence = self.router.route("")
        self.assertEqual(confidence, 0.0)
    
    def test_confidence_threshold(self):
        """Проверка порога уверенности."""
        self.assertTrue(self.router.is_confident(0.75))
        self.assertTrue(self.router.is_confident(0.95))
        self.assertFalse(self.router.is_confident(0.74))
        self.assertFalse(self.router.is_confident(0.5))
    
    def test_clarifying_questions(self):
        """Получение уточняющих вопросов."""
        questions = self.router.get_clarifying_questions(Scenario.RISK_TABLE)
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)
    
    def test_context_with_file(self):
        """Контекст с файлом повышает score."""
        context = {'has_file': True}
        scenario1, confidence1 = self.router.route("анализ договора")
        scenario2, confidence2 = self.router.route("анализ договора", context)
        
        # С файлом уверенность должна быть выше или равна
        self.assertGreaterEqual(confidence2, confidence1)
    
    def test_case_insensitive_matching(self):
        """Маршрутизация не зависит от регистра."""
        scenario1, conf1 = self.router.route("ТАБЛИЦА РИСКОВ")
        scenario2, conf2 = self.router.route("таблица рисков")
        scenario3, conf3 = self.router.route("Таблица Рисков")
        
        self.assertEqual(scenario1, scenario2)
        self.assertEqual(scenario2, scenario3)


if __name__ == '__main__':
    unittest.main()
