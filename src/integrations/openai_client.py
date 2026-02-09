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
        
        # Основные реквизиты
        parts.append(f"**ИНН:** {data.get('inn', 'не указан')}")
        parts.append(f"**КПП:** {data.get('kpp', 'не указан')}")
        parts.append(f"**ОГРН:** {data.get('ogrn', 'не указан')}")
        if data.get("ogrn_date"):
            parts.append(f"**Дата ОГРН:** {data['ogrn_date']}")
        if data.get("type"):
            parts.append(f"**Тип:** {data['type']}")

        # Название
        name = data.get("name") or {}
        if name.get("full_with_opf"):
            parts.append(f"**Полное название:** {name['full_with_opf']}")
        if name.get("short_with_opf"):
            parts.append(f"**Краткое название:** {name['short_with_opf']}")
        if name.get("latin"):
            parts.append(f"**Латинское название:** {name['latin']}")

        # ОПФ
        opf = data.get("opf") or {}
        if opf.get("full"):
            parts.append(f"**ОПФ:** {opf['full']}")

        # Статус
        state = data.get("state") or {}
        if state.get("status"):
            parts.append(f"**Статус:** {state['status']}")
        if state.get("registration_date"):
            parts.append(f"**Дата регистрации:** {state['registration_date']}")
        if state.get("liquidation_date"):
            parts.append(f"**Дата ликвидации:** {state['liquidation_date']}")
        if state.get("actuality_date"):
            parts.append(f"**Актуальность данных:** {state['actuality_date']}")

        # Адрес
        address = data.get("address") or {}
        if address.get("value"):
            parts.append(f"**Адрес:** {address['value']}")

        # Руководство
        mgmt = data.get("management")
        if mgmt:
            parts.append(f"**Руководитель:** {mgmt.get('name', 'не указан')} ({mgmt.get('post', 'должность не указана')})")

        # Уставный капитал
        capital = data.get("capital")
        if capital:
            parts.append(f"**Уставный капитал:** {capital.get('value', '—')} ({capital.get('type', '')})")

        # ОКВЭД
        if data.get("okved"):
            parts.append(f"**ОКВЭД (основной):** {data['okved']}")
        okveds = data.get("okveds")
        if okveds:
            codes_str = ", ".join(
                f"{o.get('code', '')}" + (f" ({o['name']})" if o.get('name') else "")
                for o in okveds[:10]
            )
            parts.append(f"**Все ОКВЭД:** {codes_str}")

        # Классификаторы
        for code_name, label in [("okpo", "ОКПО"), ("okato", "ОКАТО"),
                                 ("oktmo", "ОКТМО"), ("okogu", "ОКОГУ"),
                                 ("okfs", "ОКФС")]:
            val = data.get(code_name)
            if val:
                parts.append(f"**{label}:** {val}")

        # Филиалы
        if data.get("branch_type"):
            parts.append(f"**Тип филиала:** {data['branch_type']}")
        if data.get("branch_count"):
            parts.append(f"**Количество филиалов:** {data['branch_count']}")

        # Количество сотрудников
        if data.get("employee_count") is not None:
            parts.append(f"**Количество сотрудников:** {data['employee_count']}")

        # Финансовые данные
        finance = data.get("finance")
        if finance:
            parts.append("\n**Финансовые показатели:**")
            if finance.get("year"):
                parts.append(f"- Год: {finance['year']}")
            if finance.get("tax_system"):
                parts.append(f"- Система налогообложения: {finance['tax_system']}")
            if finance.get("revenue") is not None:
                parts.append(f"- Выручка: {finance['revenue']}")
            if finance.get("income") is not None:
                parts.append(f"- Доход: {finance['income']}")
            if finance.get("expense") is not None:
                parts.append(f"- Расходы: {finance['expense']}")
            if finance.get("debt") is not None:
                parts.append(f"- Задолженность: {finance['debt']}")
            if finance.get("penalty") is not None:
                parts.append(f"- Штрафы: {finance['penalty']}")
        else:
            parts.append("\n⚠️ **Финансовые данные отсутствуют в ответе DaData**")

        # Учредители
        founders = data.get("founders")
        if founders:
            parts.append("\n**Учредители:**")
            for f in founders[:10]:
                fname = f.get("name") or ""
                fio = f.get("fio")
                if fio:
                    fname = " ".join(
                        filter(None, [fio.get("surname"), fio.get("name"), fio.get("patronymic")])
                    ) or fname
                share = f.get("share")
                share_str = ""
                if share and share.get("value"):
                    share_str = f" ({share['value']}%)" if share.get("type") == "PERCENT" else f" (доля: {share['value']})"
                parts.append(f"- {fname}{share_str} [тип: {f.get('type', '—')}]")

        # Руководители (managers)
        managers = data.get("managers")
        if managers:
            parts.append("\n**Руководители:**")
            for m in managers[:10]:
                mname = m.get("name") or ""
                fio = m.get("fio")
                if fio:
                    mname = " ".join(
                        filter(None, [fio.get("surname"), fio.get("name"), fio.get("patronymic")])
                    ) or mname
                parts.append(f"- {mname} — {m.get('post', '—')}")

        # Лицензии
        licenses = data.get("licenses")
        if licenses:
            parts.append(f"\n**Лицензии ({len(licenses)}):**")
            for lic in licenses[:5]:
                num = lic.get("number", "—")
                activities = lic.get("activities")
                act_str = ", ".join(activities) if activities else ""
                parts.append(f"- №{num}: {act_str}")

        # Контакты
        phones = data.get("phones")
        if phones:
            parts.append(f"**Телефоны:** {', '.join(phones[:5])}")
        emails = data.get("emails")
        if emails:
            parts.append(f"**Email:** {', '.join(emails[:5])}")

        # Правопредшественники / правопреемники
        predecessors = data.get("predecessors")
        if predecessors:
            parts.append("\n**Правопредшественники:**")
            for p in predecessors:
                parts.append(f"- {p.get('name', '—')} (ИНН {p.get('inn', '—')})")

        successors = data.get("successors")
        if successors:
            parts.append("\n**Правопреемники:**")
            for s in successors:
                parts.append(f"- {s.get('name', '—')} (ИНН {s.get('inn', '—')})")
        
        return "\n".join(parts)


# Глобальный экземпляр клиента
openai_client = OpenAIClient()
