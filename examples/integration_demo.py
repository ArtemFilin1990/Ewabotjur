"""
Демонстрационный пример интеграции всех модулей.

Показывает, как использовать все компоненты вместе:
- Security (контроль доступа)
- File processing (извлечение текста из документов)
- Router (определение сценария)
- Prompts (генерация промптов с контекстом)
- Document generation (создание выходных документов)
"""

import io
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.security.access_control import AccessController
from src.files.index import FileProcessor, DocumentGenerator
from src.router.index import Router, Scenario
from src.prompts.index import PromptLoader, PromptType
from src.db.index import CaseContext, FileMetadata


async def demo_workflow():
    """Демонстрация полного рабочего процесса."""
    
    print("=" * 80)
    print("ДЕМО: Полный рабочий процесс Ewabotjur")
    print("=" * 80)
    
    # 1. БЕЗОПАСНОСТЬ: Проверка доступа
    print("\n1. ПРОВЕРКА ДОСТУПА")
    print("-" * 80)
    
    access_controller = AccessController("123456,789012")
    
    allowed_user = 123456
    blocked_user = 999999
    
    print(f"Пользователь {allowed_user}: {'✅ Доступ разрешён' if access_controller.is_allowed(allowed_user) else '❌ Доступ запрещён'}")
    print(f"Пользователь {blocked_user}: {'✅ Доступ разрешён' if access_controller.is_allowed(blocked_user) else '❌ Доступ запрещён'}")
    
    # 2. ОБРАБОТКА ФАЙЛА: Извлечение текста
    print("\n2. ОБРАБОТКА ФАЙЛА")
    print("-" * 80)
    
    processor = FileProcessor()
    
    # Симулируем текстовый файл договора
    contract_text = """
    ДОГОВОР ПОСТАВКИ №123 от 01.01.2024
    
    Поставщик: ООО "Компания А", ИНН 1234567890
    Покупатель: ООО "Компания Б", ИНН 0987654321
    
    Предмет договора: Поставка оборудования
    Цена: 1 000 000 рублей
    Срок поставки: 30 дней с даты подписания
    
    Ответственность:
    - За просрочку поставки - неустойка 0.1% в день
    - За некачественный товар - возврат и штраф
    
    Форс-мажор: не предусмотрен
    """
    
    file_buffer = io.BytesIO(contract_text.encode('utf-8'))
    extracted_text = processor.parse_text(file_buffer)
    
    print(f"Извлечено {len(extracted_text)} символов")
    print(f"Первые 200 символов:\n{extracted_text[:200]}...")
    
    # 3. МАРШРУТИЗАЦИЯ: Определение сценария
    print("\n3. ОПРЕДЕЛЕНИЕ СЦЕНАРИЯ")
    print("-" * 80)
    
    router = Router()
    
    # Тестируем разные запросы
    test_queries = [
        "Создай таблицу рисков по этому договору",
        "Проверь договор на соответствие ГК РФ",
        "Подготовь ответ на претензию",
        "Проверь ИНН 1234567890",
    ]
    
    for query in test_queries:
        scenario, confidence = router.route(query)
        print(f"Запрос: '{query}'")
        print(f"  → Сценарий: {scenario.value}")
        print(f"  → Уверенность: {confidence:.0%}")
        print(f"  → Авто-запуск: {'✅ Да' if router.is_confident(confidence) else '❌ Нет (нужны уточнения)'}")
        print()
    
    # 4. ГЕНЕРАЦИЯ ПРОМПТА: Подстановка контекста
    print("\n4. ГЕНЕРАЦИЯ ПРОМПТА")
    print("-" * 80)
    
    prompt_loader = PromptLoader()
    
    # Создаём контекст для промпта
    context = {
        'user_input': 'Создай таблицу рисков по договору',
        'extracted_text': extracted_text,
        'my_company': {
            'inn': '0987654321',
            'name': 'ООО "Компания Б"'
        },
        'counterparty': {
            'inn': '1234567890',
            'name': 'ООО "Компания А"',
            'risk_score': 0.3
        }
    }
    
    rendered_prompt = prompt_loader.render_prompt(PromptType.RISK_TABLE, context)
    
    print(f"Сгенерирован промпт для сценария: RISK_TABLE")
    print(f"Длина промпта: {len(rendered_prompt)} символов")
    print(f"\nПервые 500 символов:\n{rendered_prompt[:500]}...")
    
    # 5. СОЗДАНИЕ КЕЙСА: Структура данных
    print("\n5. СОЗДАНИЕ КЕЙСА")
    print("-" * 80)
    
    case_context = CaseContext(
        my_company={
            'inn': '0987654321',
            'name': 'ООО "Компания Б"'
        },
        counterparty={
            'inn': '1234567890',
            'name': 'ООО "Компания А"'
        },
        files=[
            FileMetadata(
                file_id='file_123',
                name='Договор_поставки.txt',
                size=len(contract_text),
                mime_type='text/plain',
                uploaded_at=datetime.now(),
                extracted_text=extracted_text,
                extraction_status='success'
            )
        ],
        scenario='risk_table'
    )
    
    print(f"Кейс создан:")
    print(f"  - Моя компания: {case_context.my_company['name']}")
    print(f"  - Контрагент: {case_context.counterparty['name']}")
    print(f"  - Файлов загружено: {len(case_context.files)}")
    print(f"  - Текста извлечено: {len(case_context.files[0].extracted_text)} символов")
    print(f"  - Сценарий: {case_context.scenario}")
    
    # 6. ГЕНЕРАЦИЯ ДОКУМЕНТОВ: Создание выходных файлов
    print("\n6. ГЕНЕРАЦИЯ ДОКУМЕНТОВ")
    print("-" * 80)
    
    generator = DocumentGenerator()
    
    # Пример 1: XLSX таблица рисков
    print("Генерация XLSX таблицы рисков...")
    risks_data = {
        'columns': ['Риск', 'Уровень', 'Пункт', 'Рекомендация'],
        'rows': [
            ['Отсутствие форс-мажора', 'High', 'Общие условия', 'Добавить пункт о форс-мажоре'],
            ['Низкая неустойка за просрочку', 'Medium', 'Раздел "Ответственность"', 'Увеличить до 0.5%'],
            ['Нет условий о гарантии', 'Medium', 'Предмет договора', 'Добавить гарантийные обязательства'],
        ]
    }
    
    try:
        xlsx_bytes = generator.generate_xlsx(risks_data)
        print(f"  ✅ XLSX создан: {len(xlsx_bytes)} байт")
    except ImportError as e:
        print(f"  ⚠️  Пропущено: {e}")
    
    # Пример 2: DOCX документ
    print("\nГенерация DOCX ответа на претензию...")
    docx_context = {
        'content': """
        ОТВЕТ НА ПРЕТЕНЗИЮ
        
        Уважаемая ООО "Компания А"!
        
        Рассмотрев Вашу претензию от 15.01.2024, сообщаем следующее:
        
        1. Требование о возврате денежных средств не обоснованно...
        2. Поставка была осуществлена в срок согласно п. 3.1 договора...
        
        С уважением,
        ООО "Компания Б"
        """
    }
    
    try:
        docx_bytes = generator.generate_docx(context=docx_context)
        print(f"  ✅ DOCX создан: {len(docx_bytes)} байт")
    except ImportError as e:
        print(f"  ⚠️  Пропущено: {e}")
    
    # 7. УТОЧНЯЮЩИЕ ВОПРОСЫ
    print("\n7. УТОЧНЯЮЩИЕ ВОПРОСЫ")
    print("-" * 80)
    
    questions = router.get_clarifying_questions(Scenario.RISK_TABLE)
    print(f"Если уверенность низкая, бот задаст вопросы:")
    for i, question in enumerate(questions, 1):
        print(f"  {i}. {question}")
    
    print("\n" + "=" * 80)
    print("ДЕМО ЗАВЕРШЕНО")
    print("=" * 80)
    print("\nВсе модули успешно интегрированы:")
    print("  ✅ Security - контроль доступа")
    print("  ✅ File Processing - извлечение текста")
    print("  ✅ Router - определение сценария")
    print("  ✅ Prompts - генерация промптов")
    print("  ✅ Data Models - структура кейса")
    print("  ✅ Document Generation - создание файлов")


if __name__ == '__main__':
    # Запускаем демо
    asyncio.run(demo_workflow())
