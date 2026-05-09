FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Non-root user — enterprise security baseline
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .
USER appuser

# Cloud Run injects PORT (default 8080). Bind 0.0.0.0.
# --workers tuned for Cloud Run's 1-vCPU default; --threads for I/O-bound webhook work.
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} \
    --workers 1 --threads 8 --timeout 0 \
    --access-logfile - --error-logfile - \
    main:app