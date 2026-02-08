"""
Утилита для парсинга ИНН из текста
"""
import re
from typing import Optional, List

# Pre-compiled pattern for extracting INN (10 or 12 digits surrounded by word boundaries)
_INN_PATTERN = re.compile(r'\b\d{10}\b|\b\d{12}\b')


def extract_inn(text: str) -> Optional[str]:
    """
    Извлечение ИНН из текста
    
    ИНН может быть:
    - 10 цифр для юридических лиц
    - 12 цифр для индивидуальных предпринимателей
    
    Args:
        text: Текст для поиска
        
    Returns:
        Первый найденный ИНН или None
    """
    match = _INN_PATTERN.search(text)
    if match:
        return match.group()
    return None


def extract_all_inns(text: str) -> List[str]:
    """
    Извлечение всех ИНН из текста
    
    Args:
        text: Текст для поиска
        
    Returns:
        Список найденных ИНН
    """
    return _INN_PATTERN.findall(text)


def validate_inn(inn: str) -> bool:
    """
    Базовая валидация ИНН
    
    Args:
        inn: Строка с ИНН
        
    Returns:
        True если ИНН валиден
    """
    # Проверка длины
    if len(inn) not in [10, 12]:
        return False
    
    # Проверка что все символы - цифры
    if not inn.isdigit():
        return False
    
    # Проверка контрольной суммы для 10-значного ИНН (юр. лица)
    if len(inn) == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn[i]) * coefficients[i] for i in range(9)) % 11 % 10
        return checksum == int(inn[9])
    
    # Проверка контрольной суммы для 12-значного ИНН (ИП)
    if len(inn) == 12:
        coefficients_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum_11 = sum(int(inn[i]) * coefficients_11[i] for i in range(10)) % 11 % 10
        
        coefficients_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum_12 = sum(int(inn[i]) * coefficients_12[i] for i in range(11)) % 11 % 10
        
        return checksum_11 == int(inn[10]) and checksum_12 == int(inn[11])
    
    return False
