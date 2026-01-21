"""
Модуль канонических промптов для юридических сценариев.

Загрузка и управление системными промптами для каждого из 9 сценариев.
"""

from typing import Dict
from pathlib import Path
from enum import Enum


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
    """Загрузчик канонических промптов."""
    
    def __init__(self, prompts_dir: Path = None):
        """
        Инициализация загрузчика промптов.
        
        Args:
            prompts_dir: Путь к директории с промптами
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "canonical"
        self.prompts_dir = prompts_dir
        self._cache: Dict[PromptType, str] = {}
    
    def load_prompt(self, prompt_type: PromptType) -> str:
        """
        Загрузка промпта для указанного сценария.
        
        Args:
            prompt_type: Тип промпта
        
        Returns:
            Текст системного промпта
        """
        if prompt_type in self._cache:
            return self._cache[prompt_type]
        
        # TODO: Реализовать загрузку промпта из файла
        prompt = f"# Системный промпт для {prompt_type.value}\n\nTODO: Загрузить из файла"
        self._cache[prompt_type] = prompt
        
        return prompt
    
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
