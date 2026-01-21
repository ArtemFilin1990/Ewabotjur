"""
OpenAI Service для интеграции с OpenAI API
Обеспечивает генерацию юридических документов и анализ
"""

import os
import logging
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
import asyncio
import json

logger = logging.getLogger(__name__)


class OpenAIService:
    """Сервис для работы с OpenAI API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Инициализация OpenAI сервиса
        
        Args:
            api_key: API ключ OpenAI (если не указан, берется из env)
            model: Модель для использования (по умолчанию из env или gpt-4)
            timeout: Таймаут запросов в секундах
        """
        self.api_key = api_key or os.getenv('LLM_API_KEY')
        self.model = model or os.getenv('LLM_MODEL', 'gpt-4')
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured. Set LLM_API_KEY")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Канонические промты из SRS
        self.canonical_prompts = {
            "DOC_STRUCTURE": "🧱 Структура юридического документа",
            "DISPUTE_PREP": "🔍 Подготовка к спору",
            "LEGAL_OPINION": "✍️ Юридическое заключение",
            "CLIENT_EXPLAIN": "⚖️ Объяснение клиенту спорной ситуации",
            "CLAIM_REPLY": "📬 Ответ на претензию",
            "BIZ_CORR_CONTEXT": "📋 Юридическая деловая переписка — сбор контекста",
            "CONTRACT_AGENT": "🧩 Юридический агент по договорам РФ",
            "RISK_TABLE": "📑 Таблица рисков",
            "CASELAW_ANALYTICS": "📊 Анализ судебной практики"
        }
    
    async def generate_completion(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Генерация ответа от OpenAI
        
        Args:
            prompt: Промт пользователя
            system_message: Системное сообщение
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            
        Returns:
            Сгенерированный текст
        """
        messages = []
        
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ),
                timeout=self.timeout
            )
            
            return response.choices[0].message.content
            
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при запросе к OpenAI API (timeout={self.timeout}s)")
            raise
        except Exception as e:
            logger.error(f"Ошибка при генерации текста OpenAI: {e}")
            raise
    
    async def generate_legal_document(
        self,
        scenario: str,
        context: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """
        Генерация юридического документа по сценарию
        
        Args:
            scenario: Тип сценария (DOC_STRUCTURE, DISPUTE_PREP, и т.д.)
            context: Контекст с дополнительными данными
            user_input: Запрос пользователя
            
        Returns:
            Словарь с результатом генерации
        """
        scenario_name = self.canonical_prompts.get(scenario, "Общий сценарий")
        
        system_message = f"""Ты - опытный юрист-эксперт по российскому праву.
Тебе нужно помочь пользователю в сценарии: {scenario_name}

Важно:
- Строго следуй формату, требуемому сценарием
- Используй только актуальное российское законодательство
- Будь конкретен и практичен
- Не давай гарантий результата
- Укажи необходимые уточнения, если данных недостаточно"""
        
        # Формируем промт с контекстом
        prompt_parts = [f"Запрос пользователя: {user_input}"]
        
        if context.get('company_data'):
            prompt_parts.append("\nДанные компании (DaData):")
            prompt_parts.append(self._format_company_data(context['company_data']))
        
        if context.get('file_content'):
            prompt_parts.append(f"\nСодержимое файла:\n{context['file_content']}")
        
        if context.get('additional_info'):
            prompt_parts.append(f"\nДополнительная информация:\n{context['additional_info']}")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            result_text = await self.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3  # Более детерминированный результат для юридических документов
            )
            
            result = {
                "scenario": scenario,
                "scenario_name": scenario_name,
                "document": result_text,
                "success": True
            }
            
            logger.info(f"Успешно сгенерирован документ для сценария {scenario}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при генерации юридического документа: {e}")
            raise
    
    async def analyze_with_dadata(
        self,
        company_data: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> str:
        """
        Анализ данных компании с использованием DaData и генерация отчета
        
        Args:
            company_data: Данные компании из DaData
            risk_assessment: Результаты скоринга
            
        Returns:
            Текстовый отчет
        """
        system_message = """Ты - эксперт по due diligence и проверке контрагентов.
Создай краткий и понятный отчет о компании на основе данных DaData."""
        
        prompt = f"""Проанализируй компанию и создай краткий отчет:

{self._format_company_data(company_data)}

Скоринг рисков:
- Уровень риска: {risk_assessment['risk_level']}
- Оценка: {risk_assessment['score']}/100
- Факторы риска: {', '.join(risk_assessment['risk_factors']) if risk_assessment['risk_factors'] else 'Не выявлены'}

Создай структурированный отчет с разделами:
1. Общая информация
2. Оценка рисков
3. Рекомендации"""
        
        try:
            result = await self.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе данных компании: {e}")
            raise
    
    def _format_company_data(self, company_data: Dict[str, Any]) -> str:
        """Форматирование данных компании для промпта"""
        lines = []
        data = company_data.get('data', {})
        
        lines.append(f"Название: {data.get('name', {}).get('short_with_opf', 'Неизвестно')}")
        lines.append(f"ИНН: {data.get('inn', 'Не указан')}")
        lines.append(f"ОГРН: {data.get('ogrn', 'Не указан')}")
        
        status = data.get('state', {}).get('status')
        if status:
            lines.append(f"Статус: {status}")
        
        reg_date = data.get('state', {}).get('registration_date')
        if reg_date:
            lines.append(f"Дата регистрации: {reg_date}")
        
        address = data.get('address', {}).get('value')
        if address:
            lines.append(f"Адрес: {address}")
        
        return "\n".join(lines)
    
    async def route_scenario(
        self,
        user_input: str,
        available_scenarios: List[str]
    ) -> Dict[str, Any]:
        """
        Определение подходящего сценария для запроса пользователя (AI-роутинг)
        
        Args:
            user_input: Ввод пользователя
            available_scenarios: Список доступных сценариев
            
        Returns:
            Словарь с определенным сценарием и уверенностью
        """
        system_message = """Ты - эксперт по классификации юридических запросов.
Определи, какой сценарий наилучшим образом подходит для запроса пользователя."""
        
        scenarios_list = "\n".join([f"{i+1}. {scenario}" for i, scenario in enumerate(available_scenarios)])
        
        user_prompt = f"""Проанализируй запрос пользователя и определи наиболее подходящий сценарий.

Запрос пользователя: "{user_input}"

Доступные сценарии:
{scenarios_list}

Ответь в формате JSON:
{{
    "scenario": "название_сценария",
    "confidence": 0.85,
    "reasoning": "краткое обоснование выбора"
}}
"""
        
        try:
            response = await self.generate_completion(
                prompt=user_prompt,
                system_message=system_message,
                temperature=0.3
            )
            
            # Парсим JSON ответ
            try:
                result = json.loads(response)
            except json.JSONDecodeError as json_err:
                logger.error(f"Ошибка парсинга JSON ответа от OpenAI: {json_err}")
                logger.debug(f"Полученный ответ: {response}")
                return {
                    "scenario": None,
                    "confidence": 0.0,
                    "reasoning": "Ошибка парсинга ответа от AI"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при роутинге сценария через AI: {e}")
            # Возвращаем неопределенный результат
            return {
                "scenario": None,
                "confidence": 0.0,
                "reasoning": "Ошибка при определении сценария"
            }
