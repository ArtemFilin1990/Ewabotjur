# Базовый образ Python
FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директории для хранилища
RUN mkdir -p /app/storage

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
ENV DADATA_TOKEN=${DADATA_TOKEN}
ENV ALLOWED_CHAT_IDS=${ALLOWED_CHAT_IDS}
ENV WORKER_AUTH_TOKEN=${WORKER_AUTH_TOKEN}
ENV MEMORY_STORE_PATH=${MEMORY_STORE_PATH}

# Открытие порта API
EXPOSE 8000

# Команда запуска воркера
CMD ["python", "-m", "src.main"]
