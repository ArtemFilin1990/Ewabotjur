"""
Утилита для парсинга ИНН из текста
"""
import re
from typing import Optional, List


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
    # Паттерн для поиска ИНН (10 или 12 цифр)
    # Ищем последовательность цифр, окруженную границами слов
    pattern = r'\b\d{10}\b|\b\d{12}\b'
    
    matches = re.findall(pattern, text)
    
    if matches:
        # Возвращаем первый найденный ИНН
        inn = matches[0]
        
        # Базовая валидация (проверка контрольной суммы можно добавить)
        if len(inn) in [10, 12]:
            return inn
    
    return None


def extract_all_inns(text: str) -> List[str]:
    """
    Извлечение всех ИНН из текста
    
    Args:
        text: Текст для поиска
        
    Returns:
        Список найденных ИНН
    """
    pattern = r'\b\d{10}\b|\b\d{12}\b'
    matches = re.findall(pattern, text)
    
    # Фильтрация по длине
    return [inn for inn in matches if len(inn) in [10, 12]]


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
