FROM python:3.11-slim

# Avoid /.cache permission errors on restricted build platforms (Amvera)
ENV HOME=/tmp
ENV XDG_CACHE_HOME=/tmp/.cache
ENV PIP_CACHE_DIR=/tmp/pip-cache
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN mkdir -p /tmp/.cache /tmp/pip-cache

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
