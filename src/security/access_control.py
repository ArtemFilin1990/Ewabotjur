"""
Контроль доступа к боту.

Реализует whitelist middleware для ограничения доступа.
"""

import os
from typing import Set, Optional


class AccessController:
    """Контроллер доступа на основе whitelist."""
    
    def __init__(self, allowed_ids: Optional[str] = None):
        """
        Инициализация контроллера доступа.
        
        Args:
            allowed_ids: Строка с разделёнными запятыми ID пользователей.
                        Если None, берётся из переменной окружения ALLOWED_CHAT_IDS.
        """
        if allowed_ids is None:
            allowed_ids = os.getenv("ALLOWED_CHAT_IDS", "")
        
        # Парсим строку с ID в множество для быстрой проверки
        self.allowed_ids: Set[str] = set()
        if allowed_ids:
            self.allowed_ids = {
                id.strip() 
                for id in allowed_ids.split(",") 
                if id.strip()
            }
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Проверка доступа пользователя.
        
        Args:
            user_id: Telegram ID пользователя
        
        Returns:
            True если пользователь в whitelist, False иначе
        """
        # Если список пуст, доступ открыт всем (режим public)
        if not self.allowed_ids:
            return True
        
        return str(user_id) in self.allowed_ids
    
    def add_user(self, user_id: int):
        """
        Добавление пользователя в whitelist.
        
        Args:
            user_id: Telegram ID пользователя
        """
        self.allowed_ids.add(str(user_id))
    
    def remove_user(self, user_id: int):
        """
        Удаление пользователя из whitelist.
        
        Args:
            user_id: Telegram ID пользователя
        """
        self.allowed_ids.discard(str(user_id))
    
    def get_allowed_users(self) -> Set[str]:
        """
        Получение списка разрешённых пользователей.
        
        Returns:
            Множество ID разрешённых пользователей
        """
        return self.allowed_ids.copy()


async def check_access(update, access_controller: Optional[AccessController] = None) -> bool:
    """
    Middleware функция для проверки доступа.
    
    Использует для Telegram Bot API (python-telegram-bot или aiogram).
    
    Args:
        update: Update объект от Telegram
        access_controller: Экземпляр AccessController.
                          Если None, создаётся новый из переменных окружения.
    
    Returns:
        True если доступ разрешён, False если запрещён
    
    Example:
        @dp.message_handler()
        async def handle_message(update):
            if not await check_access(update):
                await update.message.reply_text("⛔ Доступ запрещён.")
                return
            # Обработка сообщения
    """
    if access_controller is None:
        access_controller = AccessController()
    
    # Получаем user_id из update (работает для aiogram и python-telegram-bot)
    user_id = None
    if hasattr(update, 'effective_user') and update.effective_user:
        user_id = update.effective_user.id
    elif hasattr(update, 'from_user') and update.from_user:
        user_id = update.from_user.id
    elif hasattr(update, 'message') and update.message and hasattr(update.message, 'from_user'):
        user_id = update.message.from_user.id
    
    if user_id is None:
        # Не удалось получить user_id - блокируем доступ
        return False
    
    return access_controller.is_allowed(user_id)
