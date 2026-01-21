"""
Telegram Bot Юрист - Главный файл
Интеграция DaData и OpenAI для юридического бота
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from bot.services.dadata_service import DaDataService
from bot.services.openai_service import OpenAIService

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class JuristBot:
    """Основной класс Telegram бота Юрист"""
    
    def __init__(self):
        """Инициализация бота и сервисов"""
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        
        # Инициализация сервисов
        self.dadata_service = DaDataService()
        self.openai_service = OpenAIService()
        
        # Хранилище для контекста пользователей (в продакшене использовать БД)
        self.user_contexts: Dict[int, Dict[str, Any]] = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        
        # Инициализируем контекст пользователя
        self.user_contexts[user_id] = {
            'scenario': None,
            'mode': 'text',
            'history': []
        }
        
        welcome_message = """👋 Добро пожаловать в Telegram-бота «Юрист»!

Я помогу вам с:
🧱 Структурой юридических документов
🔍 Подготовкой к спорам
✍️ Юридическими заключениями
⚖️ Объяснением спорных ситуаций
📬 Ответами на претензии
📋 Деловой перепиской
🧩 Проверкой договоров РФ
📑 Таблицами рисков
📊 Анализом судебной практики
🏢 Проверкой контрагентов (DaData)

Используйте /help для примеров или просто напишите свой запрос!"""
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = """📖 Примеры использования:

1️⃣ Проверка компании:
"Проверь ИНН 7707083893"
"Найди данные по ОГРН 1027700132195"

2️⃣ Юридические документы:
"Составь структуру искового заявления о взыскании долга"
"Помоги подготовиться к спору по договору поставки"

3️⃣ Анализ:
"Создай таблицу рисков по договору [приложите файл]"
"Проанализируй судебную практику за 2023 год по спорам о взыскании"

Команды:
/start - Начать работу
/help - Помощь
/prompts - Все доступные сценарии
/status - Статус бота"""
        
        await update.message.reply_text(help_message)
    
    async def prompts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /prompts - показать все сценарии"""
        prompts_message = """📋 Доступные сценарии:

1. 🧱 Структура юридического документа
2. 🔍 Подготовка к спору
3. ✍️ Юридическое заключение
4. ⚖️ Объяснение клиенту спорной ситуации
5. 📬 Ответ на претензию
6. 📋 Юридическая деловая переписка — сбор контекста
7. 🧩 Юридический агент по договорам РФ
8. 📑 Таблица рисков
9. 📊 Анализ судебной практики
🏢 Проверка контрагента (DaData)

Выберите сценарий или просто опишите вашу задачу!"""
        
        keyboard = [
            [InlineKeyboardButton("🧱 Структура документа", callback_data="scenario_DOC_STRUCTURE")],
            [InlineKeyboardButton("🔍 Подготовка к спору", callback_data="scenario_DISPUTE_PREP")],
            [InlineKeyboardButton("✍️ Юридическое заключение", callback_data="scenario_LEGAL_OPINION")],
            [InlineKeyboardButton("📑 Таблица рисков", callback_data="scenario_RISK_TABLE")],
            [InlineKeyboardButton("🏢 Проверка компании", callback_data="scenario_DADATA_CHECK")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(prompts_message, reply_markup=reply_markup)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        status_message = f"""✅ Статус бота:

Сервисы:
✅ OpenAI API: Подключен (модель: {self.openai_service.model})
✅ DaData API: Подключен
✅ Telegram Bot: Работает

Всего пользователей в сессии: {len(self.user_contexts)}"""
        
        await update.message.reply_text(status_message)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if query.data.startswith("scenario_"):
            scenario = query.data.replace("scenario_", "")
            
            if user_id not in self.user_contexts:
                self.user_contexts[user_id] = {}
            
            self.user_contexts[user_id]['scenario'] = scenario
            
            if scenario == "DADATA_CHECK":
                await query.edit_message_text(
                    "🏢 Проверка контрагента\n\n"
                    "Введите ИНН, ОГРН или название компании для проверки:"
                )
            else:
                scenario_name = self.openai_service.canonical_prompts.get(scenario, scenario)
                await query.edit_message_text(
                    f"Выбран сценарий: {scenario_name}\n\n"
                    f"Опишите вашу задачу или задайте вопрос:"
                )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        user_text = update.message.text
        
        # Инициализируем контекст, если его нет
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {'scenario': None}
        
        user_context = self.user_contexts[user_id]
        
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("⏳ Обрабатываю запрос...")
        
        try:
            # Проверяем, похоже ли на запрос о проверке компании
            if self._is_company_check_query(user_text):
                result = await self._handle_company_check(user_text)
                await processing_msg.edit_text(result)
                return
            
            # Если сценарий уже выбран
            if user_context.get('scenario'):
                scenario = user_context['scenario']
                result = await self._handle_scenario(scenario, user_text, {})
                await processing_msg.edit_text(result['document'])
                return
            
            # Иначе - пытаемся определить сценарий автоматически
            scenarios = list(self.openai_service.canonical_prompts.keys())
            route_result = await self.openai_service.route_scenario(user_text, scenarios)
            
            if route_result.get('confidence', 0) >= 0.75 and route_result.get('scenario'):
                # Уверенно определили сценарий - выполняем
                scenario = route_result['scenario']
                result = await self._handle_scenario(scenario, user_text, {})
                await processing_msg.edit_text(result['document'])
            else:
                # Низкая уверенность - предлагаем выбрать сценарий
                keyboard = [
                    [InlineKeyboardButton("🧱 Структура документа", callback_data="scenario_DOC_STRUCTURE")],
                    [InlineKeyboardButton("🔍 Подготовка к спору", callback_data="scenario_DISPUTE_PREP")],
                    [InlineKeyboardButton("📑 Таблица рисков", callback_data="scenario_RISK_TABLE")],
                    [InlineKeyboardButton("🏢 Проверка компании", callback_data="scenario_DADATA_CHECK")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await processing_msg.edit_text(
                    "Не смог точно определить сценарий.\n"
                    "Пожалуйста, выберите нужный сценарий:",
                    reply_markup=reply_markup
                )
        
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await processing_msg.edit_text(
                f"❌ Произошла ошибка при обработке запроса.\n"
                f"Попробуйте снова или используйте /help для примеров."
            )
    
    def _is_company_check_query(self, text: str) -> bool:
        """Проверка, является ли запрос проверкой компании"""
        text_lower = text.lower()
        keywords = ['инн', 'огрн', 'проверь', 'dadata', 'компани', 'организаци', 'реквизит']
        return any(keyword in text_lower for keyword in keywords) or text.isdigit()
    
    async def _handle_company_check(self, query: str) -> str:
        """Обработка запроса на проверку компании"""
        try:
            # Получаем карточку компании со скорингом
            result = await self.dadata_service.get_company_card(query)
            
            if not result['found']:
                return f"❌ Компания не найдена по запросу: {query}"
            
            company = result['company']
            risk = result['risk_assessment']
            
            # Генерируем детальный отчет через OpenAI
            analysis = await self.openai_service.analyze_with_dadata(company, risk)
            
            return f"""🏢 Карточка компании

{analysis}

📊 Скоринг:
• Уровень риска: {risk['risk_level']}
• Оценка: {risk['score']}/100
• ИНН: {risk['inn']}
• ОГРН: {risk['ogrn']}"""
            
        except Exception as e:
            logger.error(f"Ошибка при проверке компании: {e}")
            return f"❌ Ошибка при проверке компании: {str(e)}"
    
    async def _handle_scenario(
        self,
        scenario: str,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка конкретного сценария"""
        try:
            result = await self.openai_service.generate_legal_document(
                scenario=scenario,
                context=context,
                user_input=user_input
            )
            return result
        except Exception as e:
            logger.error(f"Ошибка при обработке сценария {scenario}: {e}")
            raise
    
    def run(self):
        """Запуск бота"""
        # Создаем приложение
        application = Application.builder().token(self.telegram_token).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("prompts", self.prompts_command))
        application.add_handler(CommandHandler("status", self.status_command))
        
        # Регистрируем обработчик callback кнопок
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Регистрируем обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Запускаем бота
        logger.info("Запуск Telegram бота Юрист...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Точка входа"""
    try:
        bot = JuristBot()
        bot.run()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()
