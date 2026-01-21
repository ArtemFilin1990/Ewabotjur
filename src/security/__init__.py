"""
Модуль безопасности и контроля доступа.

Содержит middleware для проверки доступа пользователей.
"""

from .access_control import check_access, AccessController

__all__ = ['check_access', 'AccessController']
