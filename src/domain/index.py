"""
Модуль бизнес-логики и доменных моделей.

Независимость от инфраструктуры, чистые бизнес-правила.
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class ScenarioType(Enum):
    """Типы юридических сценариев."""
    LEGAL_DOCUMENT_STRUCTURING = "legal_document_structuring"
    DISPUTE_PREPARATION = "dispute_preparation"
    LEGAL_OPINION = "legal_opinion"
    CLIENT_EXPLANATION = "client_explanation"
    CLAIM_RESPONSE = "claim_response"
    BUSINESS_CONTEXT = "business_context"
    CONTRACT_AGENT_RF = "contract_agent_rf"
    RISK_TABLE = "risk_table"
    CASE_LAW_ANALYTICS = "case_law_analytics"


class DocumentFormat(Enum):
    """Форматы документов."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    MD = "md"


class ProcessingStatus(Enum):
    """Статусы обработки запроса."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class UserRequest:
    """Запрос пользователя."""
    request_id: str
    user_id: str
    text: str
    files: List[str]
    scenario: Optional[ScenarioType] = None
    confidence: float = 0.0


@dataclass
class ProcessingResult:
    """Результат обработки запроса."""
    request_id: str
    status: ProcessingStatus
    scenario: ScenarioType
    response_text: str
    artifacts: List[str]
    metadata: dict


class BusinessRules:
    """Бизнес-правила приложения."""
    
    # Константы
    CONFIDENCE_THRESHOLD = 0.75
    MAX_FILE_SIZE_MB = 20
    SESSION_TTL_MINUTES = 60
    STORAGE_TTL_DAYS = 30
    
    @staticmethod
    def validate_confidence(confidence: float) -> bool:
        """
        Проверка достаточности уверенности для автоматической маршрутизации.
        
        Args:
            confidence: Уровень уверенности (0.0-1.0)
        
        Returns:
            True если уверенность достаточна
        """
        return confidence >= BusinessRules.CONFIDENCE_THRESHOLD
    
    @staticmethod
    def validate_file_size(size_bytes: int) -> bool:
        """
        Проверка размера файла.
        
        Args:
            size_bytes: Размер файла в байтах
        
        Returns:
            True если размер допустим
        """
        max_size_bytes = BusinessRules.MAX_FILE_SIZE_MB * 1024 * 1024
        return size_bytes <= max_size_bytes
    
    @staticmethod
    def calculate_processing_timeout(scenario: ScenarioType, has_files: bool) -> int:
        """
        Расчёт таймаута обработки запроса.
        
        Args:
            scenario: Тип сценария
            has_files: Наличие файлов
        
        Returns:
            Таймаут в секундах
        """
        base_timeout = 20 if not has_files else 120
        return base_timeout


class DomainService:
    """Сервис доменной логики."""
    
    def __init__(self):
        """Инициализация сервиса."""
        pass
    
    def validate_request(self, request: UserRequest) -> tuple[bool, Optional[str]]:
        """
        Валидация запроса пользователя.
        
        Args:
            request: Запрос пользователя
        
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        # TODO: Реализовать валидацию
        if not request.text and not request.files:
            return False, "Запрос должен содержать текст или файлы"
        
        return True, None
    
    def should_request_manual_scenario_selection(
        self,
        confidence: float
    ) -> bool:
        """
        Проверка необходимости ручного выбора сценария.
        
        Args:
            confidence: Уверенность классификатора
        
        Returns:
            True если требуется ручной выбор
        """
        return not BusinessRules.validate_confidence(confidence)


# TODO: Добавить валидаторы для различных типов данных
# TODO: Реализовать расчёт метрик
# TODO: Добавить бизнес-правила для различных сценариев
