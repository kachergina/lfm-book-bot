# Multi-stage build for School Books Marketplace Bot

# Build stage
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy installed dependencies
COPY --from=builder /install /usr/local

# Copy application code
COPY bot/ ./bot/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create data directory
RUN mkdir -p /app/data

# Create non-root user
RUN useradd --create-home --shell /bin/bash botuser
USER botuser

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Health check against the webhook HTTP server
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health')"

# Run the bot
CMD ["python", "-m", "bot.main"]