# Исправление ошибки активации виртуального окружения на Amvera

## Проблема

Вы видите повторяющуюся ошибку в логах Amvera:
```
bash: line 1: /app/venv/bin/activate: No such file or directory
```

Ошибка появляется каждые 5 минут (17:01, 17:06, 17:11, 17:17 и т.д.).

## Причина

Эта ошибка возникает из-за **неправильно настроенной задачи cron (планировщика задач)** на платформе Amvera. 

**Важно:** В приложениях на Amvera с Python runtime **НЕ ТРЕБУЕТСЯ** активировать виртуальное окружение вручную. Amvera автоматически создает и использует окружение Python на этапе сборки и запуска.

Путь `/app/venv/bin/activate` **не существует** в контейнере Amvera, потому что:
- Amvera использует собственную систему управления Python окружениями
- Virtual environment создается автоматически во время build-стадии
- На runtime-стадии все зависимости уже доступны без активации venv

## Решение

### Шаг 1: Проверьте задачи cron на Amvera

1. Войдите в [Amvera Console](https://console.amvera.io)
2. Откройте ваш проект
3. Перейдите в раздел **"Задачи"** или **"Cron Jobs"** (если такой раздел существует)
4. Найдите задачу, которая выполняется каждые 5 минут

### Шаг 2: Исправьте команду cron

Если вы нашли задачу с командой типа:
```bash
source /app/venv/bin/activate && python script.py
```

или

```bash
/app/venv/bin/activate && python script.py
```

**Замените её на:**
```bash
python script.py
```

или (если нужен полный путь):
```bash
/usr/bin/python3 script.py
```

### Шаг 3: Альтернативное решение - удалите задачу

Если вы **не знаете, зачем была создана эта задача cron**, рекомендуется её **удалить**:

1. В интерфейсе Amvera найдите список запланированных задач
2. Удалите задачу, которая вызывает ошибку
3. Сохраните изменения

### Шаг 4: Проверка

После внесения изменений:
1. Подождите 5-10 минут
2. Проверьте логи в Amvera Console
3. Ошибка больше не должна появляться

## Важные заметки

### Для автоматических задач на Amvera

Если вам нужно запускать периодические задачи (например, обновление токенов, очистка данных), используйте один из следующих подходов:

#### Вариант 1: Внутренний планировщик в приложении

Добавьте в ваше FastAPI приложение встроенный планировщик (например, `APScheduler`):

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=5)
async def scheduled_task():
    # Ваша задача
    pass

@app.on_event("startup")
async def startup():
    scheduler.start()
```

#### Вариант 2: Используйте готовые эндпоинты

Если Amvera поддерживает HTTP cron (вызов URL по расписанию), используйте его:

1. Создайте эндпоинт в вашем приложении:
```python
@app.post("/internal/scheduled-task")
async def scheduled_task(secret: str):
    if secret != os.getenv("INTERNAL_SECRET"):
        raise HTTPException(status_code=403)
    # Выполните задачу
    return {"status": "ok"}
```

2. Настройте HTTP cron в Amvera на вызов этого URL

#### Вариант 3: Внешние сервисы

Используйте внешние сервисы для планирования задач:
- [cron-job.org](https://cron-job.org)
- [EasyCron](https://www.easycron.com)
- [GitHub Actions](https://docs.github.com/en/actions) с scheduled workflows

### Проверка текущей конфигурации

Убедитесь, что ваш `amvera.yml` настроен правильно:

```yaml
meta:
  environment: python
  toolchain:
    name: pip
  version: 3.11

build:
  requirementsPath: requirements.txt

run:
  command: python -m uvicorn src.main:app --host 0.0.0.0 --port 3000
  containerPort: 3000
```

**Команда `run.command` НЕ должна содержать активацию venv!**

## Часто задаваемые вопросы

### Q: Нужно ли мне создавать venv в моем проекте?
**A:** Нет. Amvera автоматически управляет Python окружением.

### Q: Как запускать скрипты на Amvera?
**A:** Используйте прямой вызов Python: `python script.py` или `python -m module.script`

### Q: Где хранятся зависимости?
**A:** Amvera устанавливает зависимости из `requirements.txt` во время build-стадии.

### Q: Могу ли я использовать custom venv?
**A:** Технически можно, но это **не рекомендуется** и не нужно для работы приложения на Amvera.

## Дополнительная помощь

Если проблема сохраняется:

1. Проверьте логи приложения в Amvera Console
2. Обратитесь в поддержку Amvera: https://amvera.io/support
3. Создайте issue в репозитории: https://github.com/ArtemFilin1990/Ewabotjur/issues

## Связанные документы

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Инструкции по деплою на Amvera
- [AMVERA_ENV_VARS.md](./AMVERA_ENV_VARS.md) - Настройка переменных окружения
- [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) - Чеклист для production деплоя
