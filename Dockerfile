# Multi-stage build for Amvera deployment
FROM python:3.11-slim AS base

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

# Stage 1: Dependencies
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Копирование исходного кода
COPY . .

# Создание директорий для хранилища
RUN mkdir -p /app/storage /app/data

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# ВАЖНО: приложение должно слушать process.env.PORT (для Amvera)
ENV PORT=3000

# Открытие порта
EXPOSE 3000

# Команда запуска FastAPI сервера
CMD ["python", "-m", "src.main"]
