"""
DaData API интеграция для поиска данных о компаниях по ИНН
"""
import logging
import httpx
from typing import Optional, Dict, Any

from src.config import settings

logger = logging.getLogger(__name__)


class DaDataClient:
    """Клиент для работы с DaData API"""
    
    BASE_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
    
    def __init__(self):
        self.api_key = settings.dadata_api_key
        self.secret_key = settings.dadata_secret_key
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "X-Secret": self.secret_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def find_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Поиск компании по ИНН через DaData API
        
        Args:
            inn: ИНН компании (10 или 12 цифр)
            
        Returns:
            Словарь с данными компании или None если не найдено
        """
        url = f"{self.BASE_URL}/findById/party"
        
        payload = {
            "query": inn,
            "type": "LEGAL"  # Юридическое лицо
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get("suggestions") and len(data["suggestions"]) > 0:
                    suggestion = data["suggestions"][0]
                    logger.info(f"Found company data for INN {inn}")
                    return self._parse_company_data(suggestion)
                else:
                    logger.warning(f"No data found for INN {inn}")
                    return None
        
        except httpx.HTTPStatusError as e:
            logger.error(f"DaData API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling DaData API: {e}", exc_info=True)
            raise
    
    def _parse_company_data(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсинг данных компании из ответа DaData
        
        Args:
            suggestion: Элемент из массива suggestions
            
        Returns:
            Структурированные данные компании
        """
        data = suggestion.get("data", {})
        
        # Основные данные
        result = {
            "inn": data.get("inn"),
            "kpp": data.get("kpp"),
            "ogrn": data.get("ogrn"),
            "name": {
                "full": data.get("name", {}).get("full_with_opf"),
                "short": data.get("name", {}).get("short_with_opf"),
            },
            "okved": data.get("okved"),
            "address": {
                "value": data.get("address", {}).get("value"),
                "data": data.get("address", {}).get("data", {})
            },
            "management": data.get("management"),
            "state": {
                "status": data.get("state", {}).get("status"),
                "liquidation_date": data.get("state", {}).get("liquidation_date"),
                "registration_date": data.get("state", {}).get("registration_date"),
            },
            "opf": data.get("opf"),
            "type": data.get("type"),
        }
        
        # Финансовые данные (если доступны на тарифе)
        if "finance" in data:
            result["finance"] = {
                "revenue": data.get("finance", {}).get("revenue"),
                "expense": data.get("finance", {}).get("expense"),
                "profit": data.get("finance", {}).get("profit"),
                "year": data.get("finance", {}).get("year"),
            }
        
        # Количество сотрудников
        if "employee_count" in data:
            result["employee_count"] = data.get("employee_count")
        
        return result


# Глобальный экземпляр клиента
dadata_client = DaDataClient()
