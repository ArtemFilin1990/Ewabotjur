"""
DaData Service для интеграции с DaData API
Обеспечивает поиск компаний, проверку реквизитов и базовый скоринг
"""

import os
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger(__name__)


class DaDataService:
    """Сервис для работы с DaData API"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Инициализация DaData сервиса
        
        Args:
            api_key: API ключ DaData (если не указан, берется из env)
            secret_key: Secret ключ DaData (если не указан, берется из env)
        """
        self.api_key = api_key or os.getenv('DADATA_API_KEY')
        self.secret_key = secret_key or os.getenv('DADATA_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("DaData API keys not configured. Set DADATA_API_KEY and DADATA_SECRET_KEY")
        
        self.base_url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
        self.clean_url = "https://cleaner.dadata.ru/api/v1/clean"
        
        # Простой кэш для повторяющихся запросов
        self._cache: Dict[str, Any] = {}
        self._cache_max_size = 100
    
    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов к DaData"""
        return {
            "Authorization": f"Token {self.api_key}",
            "X-Secret": self.secret_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        return self._cache.get(key)
    
    def _set_cache(self, key: str, value: Any):
        """Сохранение данных в кэш с ограничением размера"""
        if len(self._cache) >= self._cache_max_size:
            # Удаляем первый элемент (простая стратегия)
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[key] = value
    
    async def suggest_company(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск компаний по названию, ИНН или ОГРН
        
        Args:
            query: Поисковый запрос (название, ИНН, ОГРН)
            count: Количество результатов (по умолчанию 10)
            
        Returns:
            Список найденных компаний
        """
        cache_key = f"suggest_company:{query}:{count}"
        cached = self._get_cache(cache_key)
        if cached:
            logger.info(f"Возвращаем из кэша результаты для '{query}'")
            return cached
        
        url = f"{self.base_url}/suggest/party"
        payload = {
            "query": query,
            "count": count
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._get_headers()) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    suggestions = []
                    for item in data.get('suggestions', []):
                        suggestion = {
                            'value': item.get('value'),
                            'unrestricted_value': item.get('unrestricted_value'),
                            'data': item.get('data', {})
                        }
                        suggestions.append(suggestion)
                    
                    self._set_cache(cache_key, suggestions)
                    return suggestions
                    
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при запросе к DaData API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при поиске компании: {e}")
            raise
    
    async def find_by_id(self, query: str, entity_type: str = "party") -> Optional[Dict[str, Any]]:
        """
        Поиск по точному ИНН или ОГРН
        
        Args:
            query: ИНН или ОГРН
            entity_type: Тип сущности ("party" для организаций)
            
        Returns:
            Данные о компании или None
        """
        cache_key = f"find_by_id:{query}:{entity_type}"
        cached = self._get_cache(cache_key)
        if cached:
            logger.info(f"Возвращаем из кэша результат для ИНН/ОГРН '{query}'")
            return cached
        
        url = f"{self.base_url}/findById/{entity_type}"
        payload = {
            "query": query
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._get_headers()) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    suggestions = data.get('suggestions', [])
                    if not suggestions:
                        return None
                    
                    result = {
                        'value': suggestions[0].get('value'),
                        'unrestricted_value': suggestions[0].get('unrestricted_value'),
                        'data': suggestions[0].get('data', {})
                    }
                    
                    self._set_cache(cache_key, result)
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при запросе к DaData API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при поиске по ID: {e}")
            raise
    
    async def suggest_address(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Подсказка и стандартизация адресов
        
        Args:
            query: Адрес для поиска
            count: Количество результатов
            
        Returns:
            Список подсказок адресов
        """
        url = f"{self.base_url}/suggest/address"
        payload = {
            "query": query,
            "count": count
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._get_headers()) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    suggestions = []
                    for item in data.get('suggestions', []):
                        suggestion = {
                            'value': item.get('value'),
                            'unrestricted_value': item.get('unrestricted_value'),
                            'data': item.get('data', {})
                        }
                        suggestions.append(suggestion)
                    
                    return suggestions
                    
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при запросе к DaData API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при подсказке адреса: {e}")
            raise
    
    def calculate_risk_score(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Базовый скоринг компании на основе данных DaData
        
        Args:
            company_data: Данные компании из DaData
            
        Returns:
            Словарь с оценкой риска, уровнем и факторами риска
        """
        score = 100  # Начальная оценка
        risk_factors = []
        
        data = company_data.get('data', {})
        
        # Проверка статуса компании
        status = data.get('state', {}).get('status')
        if status == 'LIQUIDATING':
            score -= 50
            risk_factors.append("Компания в процессе ликвидации")
        elif status == 'LIQUIDATED':
            score -= 100
            risk_factors.append("Компания ликвидирована")
        elif status == 'BANKRUPT':
            score -= 80
            risk_factors.append("Компания признана банкротом")
        
        # Проверка наличия массового адреса
        if data.get('address', {}).get('data', {}).get('qc') == '10':
            score -= 15
            risk_factors.append("Массовый адрес регистрации")
        
        # Проверка массового руководителя
        management = data.get('management', {})
        if management and management.get('post') == 'МАССОВЫЙ РУКОВОДИТЕЛЬ':
            score -= 20
            risk_factors.append("Массовый руководитель")
        
        # Проверка возраста компании
        reg_date = data.get('state', {}).get('registration_date')
        if reg_date:
            try:
                reg_datetime = datetime.fromisoformat(reg_date.replace("Z", "+00:00"))
                age_days = (datetime.now().astimezone() - reg_datetime).days
                if age_days < 180:  # Менее 6 месяцев
                    score -= 20
                    risk_factors.append(f"Компания зарегистрирована недавно ({age_days} дней назад)")
            except (ValueError, AttributeError):
                pass
        
        # Определение уровня риска
        if score >= 80:
            risk_level = "низкий"
        elif score >= 60:
            risk_level = "средний"
        else:
            risk_level = "высокий"
        
        return {
            "score": max(0, score),  # Оценка от 0 до 100
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "company_name": data.get('name', {}).get('short_with_opf', 'Неизвестно'),
            "inn": data.get('inn'),
            "ogrn": data.get('ogrn'),
            "status": status
        }
    
    async def get_company_card(self, query: str) -> Dict[str, Any]:
        """
        Получение полной карточки компании с скорингом
        
        Args:
            query: ИНН, ОГРН или название компании
            
        Returns:
            Карточка компании со скорингом
        """
        # Сначала пробуем поиск по точному ИНН/ОГРН
        company_data = None
        
        # Если запрос похож на ИНН или ОГРН (только цифры)
        if query.isdigit():
            company_data = await self.find_by_id(query)
        
        # Если не нашли или это не ИНН/ОГРН, ищем по названию
        if not company_data:
            suggestions = await self.suggest_company(query, count=1)
            if suggestions:
                company_data = suggestions[0]
        
        if not company_data:
            return {
                "found": False,
                "query": query,
                "message": "Компания не найдена"
            }
        
        # Рассчитываем скоринг
        risk_assessment = self.calculate_risk_score(company_data)
        
        return {
            "found": True,
            "query": query,
            "company": company_data,
            "risk_assessment": risk_assessment
        }
