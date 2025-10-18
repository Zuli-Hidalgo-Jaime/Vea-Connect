# ./Dockerfile
FROM python:3.10-slim

# system deps (if any)
RUN apt-get update && apt-get install -y build-essential libpq-dev curl

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make run.sh executable and ensure it's in the correct location
RUN chmod +x run.sh && \
    ls -la run.sh

ENV DJANGO_SETTINGS_MODULE=config.settings.production \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PYTHONPATH=/app

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

# Use run.sh as the startup command
CMD ["bash", "run.sh"] 