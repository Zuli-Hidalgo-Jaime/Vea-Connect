#!/bin/bash

# run.sh - Django Application Startup Script for Docker Container
# This script is called by the Docker container to start the Django application

echo "=== DJANGO APPLICATION STARTUP ==="
echo "Timestamp: $(date)"
echo "Current directory: $(pwd)"

# Change to the application directory
cd /app || {
    echo "Error: Failed to change to /app directory"
    exit 1
}

echo "Changed to directory: $(pwd)"

# Set environment variables
export DJANGO_SETTINGS_MODULE=config.settings.production
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

echo "Environment variables set:"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "PYTHONPATH: $PYTHONPATH"

# Verify Python installation
echo "=== PYTHON VERIFICATION ==="
python3 --version
echo "Python path: $(which python3)"

# Install dependencies if needed
echo "=== DEPENDENCY INSTALLATION ==="
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip3 install -r requirements.txt || {
        echo "Error: Failed to install requirements"
        exit 1
    }
    echo "✓ Dependencies installed"
else
    echo "No requirements.txt found, skipping dependency installation"
fi

# Critical module verification
echo "=== CRITICAL MODULE VERIFICATION ==="
required_modules=(
    "django"
    "config"
    "config.wsgi"
    "gunicorn"
)

for module in "${required_modules[@]}"; do
    if ! python3 -c "import ${module%%:*}" 2>/dev/null; then
        echo "Error: Failed to import critical module ${module%%:*}"
        exit 1
    fi
    echo "✓ Module verified: ${module%%:*}"
done

# Database connection verification
echo "=== DATABASE CONNECTION VERIFICATION ==="
# Check if PostgreSQL variables are set
if [ -z "$AZURE_POSTGRESQL_NAME" ] || [ -z "$AZURE_POSTGRESQL_USERNAME" ] || [ -z "$AZURE_POSTGRESQL_PASSWORD" ] || [ -z "$AZURE_POSTGRESQL_HOST" ]; then
    echo "Error: Las variables de entorno de PostgreSQL no están configuradas:"
    echo "AZURE_POSTGRESQL_NAME: ${AZURE_POSTGRESQL_NAME:-'NO CONFIGURADA'}"
    echo "AZURE_POSTGRESQL_USERNAME: ${AZURE_POSTGRESQL_USERNAME:-'NO CONFIGURADA'}"
    echo "AZURE_POSTGRESQL_PASSWORD: ${AZURE_POSTGRESQL_PASSWORD:-'NO CONFIGURADA'}"
    echo "AZURE_POSTGRESQL_HOST: ${AZURE_POSTGRESQL_HOST:-'NO CONFIGURADA'}"
    exit 1
fi

echo "✓ Variables de PostgreSQL configuradas"
echo "Usuario de base de datos: $AZURE_POSTGRESQL_USERNAME"
echo "Host de base de datos: $AZURE_POSTGRESQL_HOST"

# Test database connection with retry logic
echo "Testing database connection..."
max_retries=5
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if python3 manage.py check --database default 2>/dev/null; then
        echo "✓ Database connection successful"
        break
    else
        retry_count=$((retry_count + 1))
        echo "Database connection attempt $retry_count failed. Retrying in 10 seconds..."
        sleep 10
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "Error: Database connection failed after $max_retries attempts"
    echo "Please check your PostgreSQL credentials and network connectivity"
    exit 1
fi

# Database migrations
echo "=== DATABASE MIGRATIONS ==="
echo "Checking for pending migrations..."
python3 manage.py showmigrations documents || {
    echo "Warning: Could not check migrations status"
}

# Force apply specific migrations for documents
echo "Applying documents migrations specifically..."
python3 manage.py migrate documents --noinput || {
    echo "Error: Documents migrations failed"
    exit 1
}

# Apply all other migrations
python3 manage.py migrate --noinput || {
    echo "Error: Database migrations failed"
    exit 1
}
echo "✓ Database migrations completed"

# Verify migrations were applied
echo "Verifying migrations..."
python3 manage.py showmigrations documents || {
    echo "Warning: Could not verify migrations"
}

# Verify database schema
echo "Verifying database schema..."
python3 -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'documents_document' 
        AND column_name IN ('processing_state', 'processing_status');
    \"\"\")
    columns = cursor.fetchall()
    print(f'Columnas encontradas en documents_document: {[col[0] for col in columns]}')
"

# Static files collection
echo "=== STATIC FILES COLLECTION ==="
mkdir -p staticfiles || {
    echo "Error: Failed to create staticfiles directory"
    exit 1
}

python3 manage.py collectstatic --noinput || {
    echo "Error: Static files collection failed"
    exit 1
}
echo "✓ Static files collected"

# Start Celery worker in background
# Comentado temporalmente hasta que Celery esté disponible en Azure
# echo "=== CELERY WORKER START ==="
# echo "Starting Celery worker..."
# celery -A config worker --loglevel=info --detach

# Gunicorn application startup
echo "=== GUNICORN APPLICATION START ==="
echo "Starting Django application with Gunicorn..."

exec gunicorn config.wsgi:application \
    --bind=0.0.0.0:8000 \
    --timeout 120 \
    --workers 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload
