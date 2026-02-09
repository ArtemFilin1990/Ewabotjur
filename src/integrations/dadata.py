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
        Парсинг данных компании из ответа DaData (максимальный тариф).

        Args:
            suggestion: Элемент из массива suggestions

        Returns:
            Структурированные данные компании со всеми доступными полями
        """
        data = suggestion.get("data", {})

        name = data.get("name") or {}
        address = data.get("address") or {}
        state = data.get("state") or {}
        opf = data.get("opf") or {}

        result: Dict[str, Any] = {
            # --- Идентификаторы ---
            "inn": data.get("inn"),
            "kpp": data.get("kpp"),
            "ogrn": data.get("ogrn"),
            "ogrn_date": data.get("ogrn_date"),
            "hid": data.get("hid"),
            "type": data.get("type"),

            # --- Наименование ---
            "name": {
                "full_with_opf": name.get("full_with_opf"),
                "short_with_opf": name.get("short_with_opf"),
                "latin": name.get("latin"),
                "full": name.get("full"),
                "short": name.get("short"),
            },

            # --- ОПФ ---
            "opf": {
                "code": opf.get("code"),
                "full": opf.get("full"),
                "short": opf.get("short"),
            },

            # --- Статус ---
            "state": {
                "status": state.get("status"),
                "code": state.get("code"),
                "actuality_date": state.get("actuality_date"),
                "registration_date": state.get("registration_date"),
                "liquidation_date": state.get("liquidation_date"),
            },

            # --- Адрес ---
            "address": {
                "value": address.get("value"),
                "unrestricted_value": address.get("unrestricted_value"),
                "data": address.get("data", {}),
            },

            # --- Филиалы ---
            "branch_type": data.get("branch_type"),
            "branch_count": data.get("branch_count"),

            # --- Руководство ---
            "management": data.get("management"),

            # --- Классификаторы ---
            "okved": data.get("okved"),
            "okved_type": data.get("okved_type"),
            "okveds": data.get("okveds"),
            "okpo": data.get("okpo"),
            "okato": data.get("okato"),
            "oktmo": data.get("oktmo"),
            "okogu": data.get("okogu"),
            "okfs": data.get("okfs"),

            # --- Количество сотрудников ---
            "employee_count": data.get("employee_count"),
        }

        # --- Уставный капитал ---
        capital = data.get("capital")
        if capital:
            result["capital"] = {
                "type": capital.get("type"),
                "value": capital.get("value"),
            }

        # --- Учредители ---
        founders = data.get("founders")
        if founders:
            result["founders"] = [
                {
                    "ogrn": f.get("ogrn"),
                    "inn": f.get("inn"),
                    "name": f.get("name"),
                    "fio": f.get("fio"),
                    "hid": f.get("hid"),
                    "type": f.get("type"),
                    "share": f.get("share"),
                }
                for f in founders
            ]

        # --- Руководители ---
        managers = data.get("managers")
        if managers:
            result["managers"] = [
                {
                    "inn": m.get("inn"),
                    "fio": m.get("fio"),
                    "post": m.get("post"),
                    "name": m.get("name"),
                    "hid": m.get("hid"),
                    "type": m.get("type"),
                }
                for m in managers
            ]

        # --- Финансовые данные ---
        finance = data.get("finance")
        if finance:
            result["finance"] = {
                "tax_system": finance.get("tax_system"),
                "income": finance.get("income"),
                "expense": finance.get("expense"),
                "revenue": finance.get("revenue"),
                "debt": finance.get("debt"),
                "penalty": finance.get("penalty"),
                "year": finance.get("year"),
            }

        # --- Контакты ---
        phones = data.get("phones")
        if phones:
            result["phones"] = [p.get("value") for p in phones if p.get("value")]

        emails = data.get("emails")
        if emails:
            result["emails"] = [e.get("value") for e in emails if e.get("value")]

        # --- Лицензии ---
        licenses = data.get("licenses")
        if licenses:
            result["licenses"] = [
                {
                    "series": lic.get("series"),
                    "number": lic.get("number"),
                    "issue_date": lic.get("issue_date"),
                    "issue_authority": lic.get("issue_authority"),
                    "suspend_date": lic.get("suspend_date"),
                    "suspend_authority": lic.get("suspend_authority"),
                    "valid_from": lic.get("valid_from"),
                    "valid_to": lic.get("valid_to"),
                    "activities": lic.get("activities"),
                    "addresses": lic.get("addresses"),
                }
                for lic in licenses
            ]

        # --- Регистрирующие органы ---
        authorities = data.get("authorities")
        if authorities:
            result["authorities"] = {}
            for key in ("fts_registration", "fts_report", "pf", "sif"):
                auth = authorities.get(key)
                if auth:
                    result["authorities"][key] = {
                        "type": auth.get("type"),
                        "code": auth.get("code"),
                        "name": auth.get("name"),
                        "address": auth.get("address"),
                    }

        # --- Документы ---
        documents = data.get("documents")
        if documents:
            result["documents"] = {}
            for key in ("fts_registration", "fts_report", "pf_registration",
                        "sif_registration", "smb"):
                doc = documents.get(key)
                if doc:
                    result["documents"][key] = doc

        # --- Правопредшественники / правопреемники ---
        predecessors = data.get("predecessors")
        if predecessors:
            result["predecessors"] = [
                {"ogrn": p.get("ogrn"), "inn": p.get("inn"), "name": p.get("name")}
                for p in predecessors
            ]

        successors = data.get("successors")
        if successors:
            result["successors"] = [
                {"ogrn": s.get("ogrn"), "inn": s.get("inn"), "name": s.get("name")}
                for s in successors
            ]

        # --- Гражданство (для ИП) ---
        citizenship = data.get("citizenship")
        if citizenship:
            result["citizenship"] = citizenship

        # --- ФИО (для ИП) ---
        fio = data.get("fio")
        if fio:
            result["fio"] = fio

        return result


# Глобальный экземпляр клиента
dadata_client = DaDataClient()
