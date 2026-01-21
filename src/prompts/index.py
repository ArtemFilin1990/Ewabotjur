"""
Модуль канонических промптов для юридических сценариев.

Загрузка и управление системными промптами для каждого из 9 сценариев.
"""

from typing import Dict, Optional, Any
from pathlib import Path
from enum import Enum
import jinja2


class PromptType(Enum):
    """Типы канонических промптов."""
    LEGAL_DOCUMENT_STRUCTURING = "legal_document_structuring"
    DISPUTE_PREPARATION = "dispute_preparation"
    LEGAL_OPINION = "legal_opinion"
    CLIENT_EXPLANATION = "client_explanation"
    CLAIM_RESPONSE = "claim_response"
    BUSINESS_CONTEXT = "business_context"
    CONTRACT_AGENT_RF = "contract_agent_rf"
    RISK_TABLE = "risk_table"
    CASE_LAW_ANALYTICS = "case_law_analytics"


class PromptLoader:
    """Загрузчик канонических промптов с поддержкой Jinja2."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Инициализация загрузчика промптов.
        
        Args:
            prompts_dir: Путь к директории с промптами
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "templates"
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[PromptType, str] = {}
        
        # Инициализация Jinja2
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.prompts_dir)),
            autoescape=False,  # Не экранируем для промптов
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def load_prompt(self, prompt_type: PromptType) -> str:
        """
        Загрузка промпта для указанного сценария.
        
        Args:
            prompt_type: Тип промпта
        
        Returns:
            Текст системного промпта (шаблон)
        """
        if prompt_type in self._cache:
            return self._cache[prompt_type]
        
        # Имя файла шаблона
        template_file = f"{prompt_type.value}.j2"
        template_path = self.prompts_dir / template_file
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
        else:
            # Fallback: базовый промпт
            prompt = self._get_default_prompt(prompt_type)
        
        self._cache[prompt_type] = prompt
        return prompt
    
    def _get_default_prompt(self, prompt_type: PromptType) -> str:
        """
        Получение базового промпта по умолчанию.
        
        Args:
            prompt_type: Тип промпта
        
        Returns:
            Базовый текст промпта
        """
        defaults = {
            PromptType.LEGAL_DOCUMENT_STRUCTURING: """Ты — юридический ассистент. Проанализируй документ и создай его структуру.

Входные данные:
{% if user_input %}Запрос: {{ user_input }}{% endif %}
{% if extracted_text %}Документ: {{ extracted_text[:5000] }}{% endif %}

Задача: Создай структурированный анализ документа с разделами, пунктами и основными положениями.""",

            PromptType.RISK_TABLE: """Ты — юридический аналитик. Создай таблицу рисков для договора.

Входные данные:
{% if user_input %}Запрос: {{ user_input }}{% endif %}
{% if extracted_text %}Договор: {{ extracted_text[:5000] }}{% endif %}
{% if my_company %}Моя компания: {{ my_company }}{% endif %}
{% if counterparty %}Контрагент: {{ counterparty }}{% endif %}

Задача: Создай таблицу рисков в формате JSON с полями: risk (описание риска), level (High/Medium/Low), clause (пункт договора), mitigation (рекомендации).""",

            PromptType.CONTRACT_AGENT_RF: """Ты — эксперт по договорному праву РФ. Проанализируй договор или помоги составить его.

Входные данные:
{% if user_input %}Запрос: {{ user_input }}{% endif %}
{% if extracted_text %}Договор: {{ extracted_text[:10000] }}{% endif %}

Задача: Проанализируй договор на соответствие законодательству РФ или помоги составить договор с учётом требований ГК РФ.""",

            PromptType.CLAIM_RESPONSE: """Ты — юрист по претензионной работе. Подготовь ответ на претензию.

Входные данные:
{% if user_input %}Контекст: {{ user_input }}{% endif %}
{% if extracted_text %}Претензия: {{ extracted_text[:5000] }}{% endif %}
{% if my_company %}Наша компания: {{ my_company }}{% endif %}
{% if counterparty %}Контрагент: {{ counterparty }}{% endif %}

Задача: Составь профессиональный ответ на претензию с обоснованием позиции.""",
        }
        
        return defaults.get(prompt_type, f"# Промпт для {prompt_type.value}\n\n{{{{ user_input }}}}")
    
    def render_prompt(self, prompt_type: PromptType, context: Dict[str, Any]) -> str:
        """
        Рендеринг промпта с подстановкой контекста через Jinja2.
        
        Args:
            prompt_type: Тип промпта
            context: Словарь с данными для подстановки
        
        Returns:
            Отрендеренный промпт с подставленными данными
        
        Example:
            context = {
                'user_input': 'Проанализируй договор',
                'extracted_text': '...',
                'my_company': {'inn': '...', 'name': '...'},
            }
            prompt = loader.render_prompt(PromptType.RISK_TABLE, context)
        """
        template_str = self.load_prompt(prompt_type)
        template = self.jinja_env.from_string(template_str)
        return template.render(**context)
    
    def get_all_prompts(self) -> Dict[PromptType, str]:
        """
        Получение всех промптов.
        
        Returns:
            Словарь {тип_промпта: текст_промпта}
        """
        return {
            prompt_type: self.load_prompt(prompt_type)
            for prompt_type in PromptType
        }


# TODO: Создать файлы с промптами для каждого сценария
# TODO: Добавить валидацию промптов
# TODO: Добавить версионирование промптов
