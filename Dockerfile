FROM python:3.11-slim

# Set environment variables to ensure pip writes cache to writable locations
ENV PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache \
    PIP_CACHE_DIR=/tmp/pip-cache \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_PROGRESS_BAR=off

# Create necessary cache directories
RUN mkdir -p /tmp/.cache /tmp/pip-cache

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port expected by the app
EXPOSE 3000

# Default command to run the FastAPI application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
