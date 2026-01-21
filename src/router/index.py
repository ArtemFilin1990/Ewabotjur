"""
Модуль маршрутизации запросов для определения юридического сценария.

Детерминированное определение сценария с порогом уверенности 75%+.
"""

from typing import Dict, Optional, Tuple, List
from enum import Enum
import re


class Scenario(Enum):
    """Канонические юридические сценарии."""
    LEGAL_DOCUMENT_STRUCTURING = "legal_document_structuring"
    DISPUTE_PREPARATION = "dispute_preparation"
    LEGAL_OPINION = "legal_opinion"
    CLIENT_EXPLANATION = "client_explanation"
    CLAIM_RESPONSE = "claim_response"
    BUSINESS_CONTEXT = "business_context"
    CONTRACT_AGENT_RF = "contract_agent_rf"
    RISK_TABLE = "risk_table"
    CASE_LAW_ANALYTICS = "case_law_analytics"
    DADATA_CARD = "dadata_card"  # Для запросов реквизитов компаний


class Router:
    """Маршрутизатор для определения сценария обработки запроса."""
    
    CONFIDENCE_THRESHOLD = 0.75
    
    # Ключевые слова для hard gates (приоритетная маршрутизация)
    HARD_GATES = {
        Scenario.DADATA_CARD: [
            r'\b(инн|огрн)\b',
            r'\b(дада|dadata)\b',
            r'\b(скоринг|реквизит)\b',
            r'\b(проверить компанию)\b',
        ],
        Scenario.RISK_TABLE: [
            r'таблиц[аеуы]?\s+риск',
            r'риск[иа]?\s+договор',
            r'оценк[аеу]?\s+риск',
        ],
        Scenario.CLAIM_RESPONSE: [
            r'ответ\s+на\s+претензи',
            r'получена\s+претензи',
            r'претензия\s+от',
        ],
        Scenario.LEGAL_OPINION: [
            r'юридическ[оеи]+\s+заключени',
            r'правов[оеи]+\s+заключени',
            r'legal\s+opinion',
        ],
        Scenario.CASE_LAW_ANALYTICS: [
            r'судебн[аяо]+\s+практик',
            r'анализ\s+практик',
            r'решени[яе]\s+суд',
        ],
        Scenario.DISPUTE_PREPARATION: [
            r'подготовк[аеу]\s+к\s+спор',
            r'контраргумент',
            r'позиция\s+оппонент',
        ],
        Scenario.CONTRACT_AGENT_RF: [
            r'(составь|подготовь|проверь)\s+договор',
            r'анализ\s+договор',
        ],
        Scenario.BUSINESS_CONTEXT: [
            r'\b(письмо|переписк)[аеуи]',
            r'\b(email|sms)\b',
            r'делов[аяо]+\s+переписк',
        ],
        Scenario.LEGAL_DOCUMENT_STRUCTURING: [
            r'структур[аеу]\s+документ',
            r'разбор\s+документ',
        ],
    }
    
    def __init__(self):
        """Инициализация роутера."""
        # Компилируем регулярные выражения для производительности
        self._compiled_gates = {}
        for scenario, patterns in self.HARD_GATES.items():
            self._compiled_gates[scenario] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def route(self, text: str, context: Optional[Dict] = None) -> Tuple[Scenario, float]:
        """
        Определение сценария для входящего запроса.
        
        Args:
            text: Текст запроса пользователя
            context: Дополнительный контекст (история, файлы и т.д.)
        
        Returns:
            Кортеж (сценарий, уверенность)
        """
        if not text:
            return Scenario.LEGAL_DOCUMENT_STRUCTURING, 0.0
        
        # Нормализуем текст
        text_lower = text.lower()
        
        # Фаза 1: Hard gates (детерминированная маршрутизация)
        for scenario, compiled_patterns in self._compiled_gates.items():
            for pattern in compiled_patterns:
                if pattern.search(text_lower):
                    # Нашли совпадение по hard gate - высокая уверенность
                    return scenario, 0.95
        
        # Фаза 2: Scoring по ключевым словам
        scores = self._calculate_scenario_scores(text_lower, context)
        
        if not scores:
            # Нет совпадений - возвращаем дефолтный сценарий
            return Scenario.LEGAL_DOCUMENT_STRUCTURING, 0.3
        
        # Сортируем по убыванию score
        sorted_scenarios = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_scenario, best_score = sorted_scenarios[0]
        
        # Проверяем конфликты (близкие топ-2)
        if len(sorted_scenarios) > 1:
            second_score = sorted_scenarios[1][1]
            # Если второй сценарий очень близок, снижаем уверенность
            if best_score - second_score < 0.15:
                best_score *= 0.8
        
        return best_scenario, min(best_score, 1.0)
    
    def _calculate_scenario_scores(
        self, 
        text: str, 
        context: Optional[Dict] = None
    ) -> Dict[Scenario, float]:
        """
        Расчёт scores для каждого сценария.
        
        Args:
            text: Нормализованный текст запроса
            context: Дополнительный контекст
        
        Returns:
            Словарь {сценарий: score}
        """
        scores = {}
        context = context or {}
        
        # Ключевые слова для каждого сценария (soft matching)
        keywords = {
            Scenario.RISK_TABLE: ['риск', 'опасност', 'проблем', 'анализ договора'],
            Scenario.CONTRACT_AGENT_RF: ['договор', 'контракт', 'соглашение', 'гк рф'],
            Scenario.CLAIM_RESPONSE: ['претензия', 'требование', 'ответ'],
            Scenario.LEGAL_OPINION: ['заключение', 'мнение', 'позиция', 'оценка'],
            Scenario.CASE_LAW_ANALYTICS: ['практика', 'суд', 'решение', 'постановление'],
            Scenario.DISPUTE_PREPARATION: ['спор', 'конфликт', 'аргумент', 'доказательств'],
            Scenario.BUSINESS_CONTEXT: ['письмо', 'ответ', 'переписка'],
            Scenario.LEGAL_DOCUMENT_STRUCTURING: ['структура', 'разбор', 'анализ'],
        }
        
        for scenario, words in keywords.items():
            score = 0.0
            matches = 0
            
            for word in words:
                if word in text:
                    matches += 1
                    score += 0.2
            
            # Бонусы
            if context.get('has_file'):
                score += 0.1
            if context.get('has_company_info'):
                score += 0.1
            
            # Штрафы
            if matches == 0:
                score = 0.0
            
            if score > 0:
                scores[scenario] = score
        
        return scores
    
    def is_confident(self, confidence: float) -> bool:
        """
        Проверка достаточности уверенности для автоматической маршрутизации.
        
        Args:
            confidence: Уровень уверенности (0.0-1.0)
        
        Returns:
            True если уверенность выше порога
        """
        return confidence >= self.CONFIDENCE_THRESHOLD
    
    def get_clarifying_questions(self, scenario: Scenario) -> List[str]:
        """
        Получение пакета уточняющих вопросов для сценария.
        
        Args:
            scenario: Сценарий
        
        Returns:
            Список вопросов
        """
        questions = {
            Scenario.LEGAL_DOCUMENT_STRUCTURING: [
                "Какой тип документа вы хотите проанализировать?",
                "В какой области права (гражданское, трудовое, корпоративное)?",
                "Нужен ли детальный разбор или общая структура?",
            ],
            Scenario.RISK_TABLE: [
                "Какой тип договора (поставка, услуги, подряд)?",
                "Вы выступаете заказчиком или исполнителем?",
                "Есть ли конкретные пункты, которые вызывают опасения?",
                "Нужна ли оценка по всем рискам или только критические?",
            ],
            Scenario.CONTRACT_AGENT_RF: [
                "Какой тип договора нужен?",
                "Кто стороны договора (ООО, ИП, физлицо)?",
                "Каков предмет договора?",
                "Какова примерная цена/стоимость?",
                "Есть ли особые условия или сроки?",
            ],
            Scenario.CLAIM_RESPONSE: [
                "Кто получил претензию (название и реквизиты)?",
                "От кого претензия (контрагент)?",
                "Какие требования заявлены и в какой срок?",
                "Какова ваша позиция (признаете/не признаете)?",
                "Есть ли документы в подтверждение позиции?",
            ],
        }
        
        return questions.get(scenario, [
            "Опишите подробнее вашу задачу.",
            "Какой результат вы ожидаете получить?",
        ])


# TODO: Реализовать правила классификации
# TODO: Добавить анализ ключевых слов
# TODO: Добавить ML-модель для классификации (опционально)
