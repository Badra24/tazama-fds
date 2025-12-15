FROM python:3.11-slim

# Install system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev netcat-openbsd curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY tazama_api_client/requirements.txt /app/requirements.txt

# Create non-root user
RUN useradd --create-home appuser

# Install Python deps
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application
COPY tazama_api_client /app/tazama_api_client

# Ensure runtime user owns files
RUN chown -R appuser:appuser /app
USER appuser

WORKDIR /app/tazama_api_client

# Expose the configured port (default 8091)
EXPOSE 8091

# Use Uvicorn in production mode (workers optional under a process manager)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8091", "--workers", "1"]
