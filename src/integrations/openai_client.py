"""
OpenAI GPT интеграция для генерации рекомендаций и анализа рисков
"""
import logging
import httpx
from typing import Dict, Any, Optional
import os

from src.config import settings
from src.utils.http import get_http_client

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Клиент для работы с OpenAI API"""
    
    BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Загрузка системного промпта
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Загрузка системного промпта из файла"""
        prompt_path = os.path.join("prompts", "inn_score.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(
                "Prompt file not found, using default",
                extra={"operation": "openai.prompt", "result": "fallback", "path": prompt_path},
            )
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Промпт по умолчанию"""
        return """Ты — эксперт по анализу контрагентов и оценке рисков при работе с компаниями.

ВАЖНЫЕ ПРАВИЛА:
1. Все факты должны браться ТОЛЬКО из предоставленных данных DaData
2. Ты НЕ должен выдумывать или додумывать информацию
3. Если данных нет в DaData - явно укажи это
4. Твоя задача - дать заключение, оценку рисков и рекомендации на основе ИМЕЮЩИХСЯ данных

Структура твоего ответа:
1. **Общая оценка** - краткий вывод о компании
2. **Выявленные риски** - список конкретных рисков на основе данных
3. **Рекомендации** - что нужно запросить у контрагента
4. **Дальнейшие действия** - что делать дальше

Если каких-то данных нет (например, финансовые показатели недоступны на тарифе), напиши:
"⚠️ Финансовые данные недоступны в DaData на текущем тарифе"
"""
    
    async def analyze_company(self, company_data: Dict[str, Any]) -> str:
        """
        Анализ компании с помощью GPT
        
        Args:
            company_data: Данные компании из DaData
            
        Returns:
            Текст с анализом и рекомендациями
        """
        # Формирование запроса для GPT
        user_message = self._format_company_data(company_data)
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        try:
            client = await get_http_client()
            # OpenAI GPT analysis can take longer than standard requests (up to 60s)
            # due to complex reasoning and generation, so we override the default timeout
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=60.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Извлечение ответа
            if data.get("choices") and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                logger.info(
                    "GPT analysis completed",
                    extra={
                        "operation": "openai.analyze",
                        "result": "success",
                        "inn": company_data.get("inn"),
                    },
                )
                return content
            else:
                logger.error(
                    "No choices in GPT response",
                    extra={"operation": "openai.analyze", "result": "error"},
                )
                return "⚠️ Ошибка: не получен ответ от GPT. Попробуйте позже."

        except httpx.HTTPStatusError as e:
            logger.error(
                "OpenAI API error",
                extra={
                    "operation": "openai.request",
                    "result": "error",
                    "status_code": e.response.status_code,
                },
                exc_info=True,
            )
            # Return user-friendly error instead of crashing
            if e.response.status_code == 401:
                return "⚠️ Ошибка конфигурации: неверный API ключ OpenAI"
            elif e.response.status_code == 429:
                return "⚠️ Превышен лимит запросов к OpenAI. Попробуйте позже."
            elif e.response.status_code >= 500:
                return "⚠️ Сервис OpenAI временно недоступен. Попробуйте позже."
            else:
                return f"⚠️ Ошибка OpenAI API (код {e.response.status_code})"
        except httpx.TimeoutException as e:
            logger.error(
                "OpenAI API timeout",
                extra={"operation": "openai.request", "result": "timeout"},
                exc_info=True,
            )
            return "⚠️ Превышено время ожидания ответа от OpenAI. Попробуйте позже."
        except Exception as e:
            logger.error(
                "Error calling OpenAI API",
                extra={"operation": "openai.request", "result": "error"},
                exc_info=True,
            )
            return f"⚠️ Непредвиденная ошибка при анализе: {str(e)}"
    
    def _format_company_data(self, data: Dict[str, Any]) -> str:
        """
        Форматирование данных компании для передачи в GPT
        
        Args:
            data: Данные компании из DaData
            
        Returns:
            Отформатированная строка с данными
        """
        parts = []
        
        parts.append("Проанализируй следующую компанию:\n")
        
        # Основные данные
        parts.append(f"**ИНН:** {data.get('inn', 'не указан')}")
        parts.append(f"**КПП:** {data.get('kpp', 'не указан')}")
        parts.append(f"**ОГРН:** {data.get('ogrn', 'не указан')}")
        
        # Название
        if data.get("name"):
            parts.append(f"**Полное название:** {data['name'].get('full', 'не указано')}")
            parts.append(f"**Краткое название:** {data['name'].get('short', 'не указано')}")
        
        # ОКВЭД
        if data.get("okved"):
            parts.append(f"**ОКВЭД:** {data['okved']}")
        
        # Адрес
        if data.get("address", {}).get("value"):
            parts.append(f"**Адрес:** {data['address']['value']}")
        
        # Руководство
        if data.get("management"):
            mgmt = data["management"]
            parts.append(f"**Руководитель:** {mgmt.get('name', 'не указан')} ({mgmt.get('post', 'должность не указана')})")
        
        # Статус
        if data.get("state"):
            state = data["state"]
            parts.append(f"**Статус:** {state.get('status', 'не указан')}")
            if state.get("registration_date"):
                parts.append(f"**Дата регистрации:** {state['registration_date']}")
            if state.get("liquidation_date"):
                parts.append(f"**Дата ликвидации:** {state['liquidation_date']}")
        
        # Финансовые данные (если есть)
        if data.get("finance"):
            finance = data["finance"]
            parts.append("\n**Финансовые показатели:**")
            parts.append(f"- Выручка: {finance.get('revenue', 'нет данных')}")
            parts.append(f"- Расходы: {finance.get('expense', 'нет данных')}")
            parts.append(f"- Прибыль: {finance.get('profit', 'нет данных')}")
            parts.append(f"- Год: {finance.get('year', 'нет данных')}")
        else:
            parts.append("\n⚠️ **Финансовые данные недоступны на текущем тарифе DaData**")
        
        # Количество сотрудников
        if data.get("employee_count"):
            parts.append(f"**Количество сотрудников:** {data['employee_count']}")
        
        return "\n".join(parts)


# Глобальный экземпляр клиента
openai_client = OpenAIClient()
