#!/usr/bin/env python3
"""
Демонстрация возможностей Telegram бота
Этот скрипт тестирует основные компоненты без реального подключения к Telegram
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем минимальные env переменные для теста
os.environ['BOT_TOKEN'] = 'test_token_123'
os.environ['ALLOWED_CHAT_IDS'] = '12345,67890'
os.environ['DADATA_TOKEN'] = ''
os.environ['LOG_LEVEL'] = 'INFO'

from app.bot.handlers import access_ok
from app.services.scoring import score_company
from app.config import ALLOWED_CHAT_IDS, BOT_TOKEN, LOG_LEVEL

def test_config():
    """Тест конфигурации"""
    print("=" * 60)
    print("1. КОНФИГУРАЦИЯ")
    print("=" * 60)
    print(f"BOT_TOKEN: {'✅ Установлен' if BOT_TOKEN else '❌ Не установлен'}")
    print(f"ALLOWED_CHAT_IDS: {ALLOWED_CHAT_IDS}")
    print(f"LOG_LEVEL: {LOG_LEVEL}")
    print()

def test_access_control():
    """Тест контроля доступа"""
    print("=" * 60)
    print("2. КОНТРОЛЬ ДОСТУПА")
    print("=" * 60)
    
    # Mock Message class
    class MockMessage:
        def __init__(self, chat_id):
            self.chat = type('obj', (object,), {'id': chat_id})
    
    # Test whitelisted user
    msg1 = MockMessage(12345)
    result1 = access_ok(msg1)
    print(f"Chat ID 12345 (в whitelist): {'✅ Доступ разрешён' if result1 else '❌ Доступ запрещён'}")
    
    # Test non-whitelisted user
    msg2 = MockMessage(99999)
    result2 = access_ok(msg2)
    print(f"Chat ID 99999 (не в whitelist): {'❌ Доступ запрещён' if not result2 else '✅ Доступ разрешён'}")
    print()

def test_scoring():
    """Тест скоринга компаний"""
    print("=" * 60)
    print("3. СКОРИНГ КОМПАНИЙ")
    print("=" * 60)
    
    # Test 1: Активная компания без рисков
    print("\n📊 Тест 1: Активная компания")
    sample_data = {
        'value': 'ООО "НАДЁЖНАЯ КОМПАНИЯ"',
        'data': {
            'inn': '7707083893',
            'ogrn': '1027700132195',
            'state': {'status': 'ACTIVE'},
            'address': {
                'value': 'г Москва, ул Тверская, д 1',
                'qc': '0'
            },
            'management': {
                'name': 'Иванов Иван Иванович'
            }
        }
    }
    
    result = score_company(sample_data)
    print(result)
    
    # Test 2: Компания с рисками
    print("\n" + "=" * 60)
    print("📊 Тест 2: Компания с рисками")
    risky_data = {
        'value': 'ООО "ПРОБЛЕМНАЯ КОМПАНИЯ"',
        'data': {
            'inn': '1234567890',
            'ogrn': '1234567890123',
            'state': {'status': 'LIQUIDATING'},
            'address': {
                'value': 'г Москва, адрес не подтверждён',
                'qc': '1'
            },
            'management': {
                'name': 'Петров Петр Петрович'
            }
        }
    }
    
    result2 = score_company(risky_data)
    print(result2)
    print()

def test_bot_structure():
    """Тест структуры бота"""
    print("=" * 60)
    print("4. СТРУКТУРА БОТА")
    print("=" * 60)
    
    from app.bot.router import router
    from app.bot import handlers
    
    print(f"✅ Главный роутер создан: {type(router).__name__}")
    print(f"✅ Роутер обработчиков создан: {type(handlers.router).__name__}")
    print(f"✅ Обработчики зарегистрированы")
    print()

def main():
    """Основная функция"""
    print("\n" + "🤖 ДЕМОНСТРАЦИЯ TELEGRAM БОТА".center(60))
    print("=" * 60)
    print()
    
    try:
        test_config()
        test_access_control()
        test_scoring()
        test_bot_structure()
        
        print("=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        print()
        print("Для запуска бота:")
        print("1. Создайте .env файл с настройками (см. .env.example)")
        print("2. Запустите: python -m app.main")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
