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
ENV TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
ENV DADATA_TOKEN=${DADATA_TOKEN}
ENV DB_URL=${DB_URL}
ENV STORAGE_PATH=${STORAGE_PATH}
ENV LLM_API_KEY=${LLM_API_KEY}

# Открытие порта для метрик (опционально)
EXPOSE 9090

# Команда запуска воркера
CMD ["python", "-m", "src.worker_main"]
