"""
Тесты для модуля безопасности.
"""

import os
import unittest
from unittest.mock import Mock
from src.security.access_control import AccessController, check_access


class TestAccessController(unittest.TestCase):
    """Тесты для AccessController."""
    
    def test_empty_whitelist_allows_everyone(self):
        """Пустой whitelist разрешает доступ всем."""
        controller = AccessController("")
        self.assertTrue(controller.is_allowed(12345))
        self.assertTrue(controller.is_allowed(67890))
    
    def test_whitelist_allows_specific_users(self):
        """Whitelist разрешает только указанным пользователям."""
        controller = AccessController("123456,789012")
        self.assertTrue(controller.is_allowed(123456))
        self.assertTrue(controller.is_allowed(789012))
        self.assertFalse(controller.is_allowed(999999))
    
    def test_whitelist_handles_spaces(self):
        """Whitelist корректно обрабатывает пробелы."""
        controller = AccessController("123456 , 789012 ")
        self.assertTrue(controller.is_allowed(123456))
        self.assertTrue(controller.is_allowed(789012))
    
    def test_add_user(self):
        """Добавление пользователя в whitelist."""
        controller = AccessController("123456")
        self.assertFalse(controller.is_allowed(789012))
        
        controller.add_user(789012)
        self.assertTrue(controller.is_allowed(789012))
    
    def test_remove_user(self):
        """Удаление пользователя из whitelist."""
        controller = AccessController("123456,789012")
        self.assertTrue(controller.is_allowed(789012))
        
        controller.remove_user(789012)
        self.assertFalse(controller.is_allowed(789012))
    
    def test_get_allowed_users(self):
        """Получение списка разрешённых пользователей."""
        controller = AccessController("123456,789012")
        allowed = controller.get_allowed_users()
        self.assertEqual(allowed, {"123456", "789012"})


class TestCheckAccessMiddleware(unittest.IsolatedAsyncioTestCase):
    """Тесты для middleware функции check_access."""
    
    async def test_check_access_with_effective_user(self):
        """Проверка доступа с effective_user (python-telegram-bot)."""
        controller = AccessController("123456")
        
        # Mock update с effective_user
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456
        
        result = await check_access(update, controller)
        self.assertTrue(result)
        
        # Проверяем запрещённого пользователя
        update.effective_user.id = 999999
        result = await check_access(update, controller)
        self.assertFalse(result)
    
    async def test_check_access_with_from_user(self):
        """Проверка доступа с from_user (aiogram)."""
        controller = AccessController("789012")
        
        # Mock update с from_user
        update = Mock()
        update.effective_user = None
        update.from_user = Mock()
        update.from_user.id = 789012
        
        result = await check_access(update, controller)
        self.assertTrue(result)
    
    async def test_check_access_without_user_id(self):
        """Проверка доступа без user_id блокируется."""
        controller = AccessController("123456")
        
        # Mock update без user_id
        update = Mock()
        update.effective_user = None
        update.from_user = None
        
        result = await check_access(update, controller)
        self.assertFalse(result)
    
    async def test_check_access_creates_default_controller(self):
        """check_access создаёт контроллер по умолчанию."""
        # Устанавливаем переменную окружения
        os.environ["ALLOWED_CHAT_IDS"] = "111111,222222"
        
        try:
            update = Mock()
            update.effective_user = Mock()
            update.effective_user.id = 111111
            
            result = await check_access(update)
            self.assertTrue(result)
            
            update.effective_user.id = 999999
            result = await check_access(update)
            self.assertFalse(result)
        finally:
            # Очищаем переменную окружения
            if "ALLOWED_CHAT_IDS" in os.environ:
                del os.environ["ALLOWED_CHAT_IDS"]


if __name__ == '__main__':
    unittest.main()
