"""
DaData API интеграция для поиска данных о компаниях по ИНН
"""
import logging
import httpx
from typing import Optional, Dict, Any

from src.config import settings
from src.utils.http import get_http_client

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
        }
        
        try:
            client = await get_http_client()
            response = await client.post(
                url,
                json=payload,
                headers=self.headers
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("suggestions"):
                suggestion = data["suggestions"][0]
                logger.info(
                    "Found company data",
                    extra={"operation": "dadata.find", "result": "success", "inn": inn},
                )
                return self._parse_company_data(suggestion)
            else:
                logger.warning(
                    "No data found",
                    extra={"operation": "dadata.find", "result": "not_found", "inn": inn},
                )
                return None
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "DaData API error",
                extra={
                    "operation": "dadata.find",
                    "result": "error",
                    "status_code": e.response.status_code,
                    "inn": inn,
                },
                exc_info=True,
            )
            raise
        except httpx.TimeoutException as e:
            logger.error(
                "DaData API timeout",
                extra={"operation": "dadata.find", "result": "timeout", "inn": inn},
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                "Error calling DaData API",
                extra={"operation": "dadata.find", "result": "error", "inn": inn},
                exc_info=True,
            )
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
        
        name = data.get("name") or {}
        address = data.get("address") or {}
        state = data.get("state") or {}
        opf = data.get("opf") or {}

        # Основные данные
        result = {
            "inn": data.get("inn"),
            "kpp": data.get("kpp"),
            "ogrn": data.get("ogrn"),
            "ogrn_date": data.get("ogrn_date"),
            "hid": data.get("hid"),
            "name": {
                "full": name.get("full") or name.get("full_with_opf"),
                "short": name.get("short") or name.get("short_with_opf"),
                "latin": name.get("latin"),
                "full_with_opf": name.get("full_with_opf"),
                "short_with_opf": name.get("short_with_opf"),
            },
            "okved": data.get("okved"),
            "okved_type": data.get("okved_type"),
            "okveds": data.get("okveds") or [],
            "address": {
                "value": address.get("value"),
                "unrestricted_value": address.get("unrestricted_value"),
                "data": address.get("data", {})
            },
            "management": data.get("management"),
            "managers": data.get("managers") or [],
            "founders": data.get("founders") or [],
            "state": {
                "status": state.get("status"),
                "code": state.get("code"),
                "actuality_date": state.get("actuality_date"),
                "liquidation_date": state.get("liquidation_date"),
                "registration_date": state.get("registration_date"),
            },
            "opf": {
                "code": opf.get("code"),
                "full": opf.get("full"),
                "short": opf.get("short"),
            },
            "type": data.get("type"),
            "branch_type": data.get("branch_type"),
            "branch_count": data.get("branch_count"),
            "okpo": data.get("okpo"),
            "okato": data.get("okato"),
            "oktmo": data.get("oktmo"),
            "okogu": data.get("okogu"),
            "okfs": data.get("okfs"),
            "capital": data.get("capital"),
            "phones": data.get("phones") or [],
            "emails": data.get("emails") or [],
            "licenses": data.get("licenses") or [],
            "authorities": data.get("authorities") or [],
            "documents": data.get("documents") or [],
            "predecessors": data.get("predecessors") or [],
            "successors": data.get("successors") or [],
            "citizenship": data.get("citizenship"),
            "fio": data.get("fio"),
        }
        
        # Финансовые данные (если доступны на тарифе)
        finance = data.get("finance")
        if finance:
            result["finance"] = {
                "revenue": finance.get("revenue"),
                "expense": finance.get("expense"),
                "profit": finance.get("profit"),
                "year": finance.get("year"),
                "tax_system": finance.get("tax_system"),
                "income": finance.get("income"),
                "debt": finance.get("debt"),
                "penalty": finance.get("penalty"),
            }
        
        # Количество сотрудников
        if "employee_count" in data:
            result["employee_count"] = data.get("employee_count")
        
        return result


# Глобальный экземпляр клиента
dadata_client = DaDataClient()
