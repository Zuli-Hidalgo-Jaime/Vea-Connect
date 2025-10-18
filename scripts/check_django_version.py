#!/usr/bin/env python3
"""
Simple Django Version Check Script
Verifies Django version and basic functionality
"""
import os
import sys
import django
from pathlib import Path

# Configure Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Selecciona settings en función del entorno (igual que manage.py)
settings_module = "config.settings.azure_production" if 'WEBSITE_HOSTNAME' in os.environ else 'config.settings.development'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

# Carga .env solo en desarrollo local y si está disponible
if 'WEBSITE_HOSTNAME' not in os.environ:
    try:
        from dotenv import load_dotenv
        print("Loading variables from .env (local mode)")
        load_dotenv('./.env')
    except ImportError:
        print("python-dotenv not installed, continuing without .env")
    except Exception as e:
        print(f"Error loading .env: {e}, continuing without .env")

try:
    django.setup()
    print(f"✅ Django configured successfully with {settings_module}")
except Exception as e:
    print(f"❌ Could not load Django settings: {e}")
    sys.exit(1)

# Check Django version
import django
print(f"📦 Django version: {django.get_version()}")

# Check if we can import basic models
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    print("✅ User model imported successfully")
except Exception as e:
    print(f"❌ Error importing User model: {e}")

try:
    from apps.documents.models import Document
    print("✅ Document model imported successfully")
except Exception as e:
    print(f"❌ Error importing Document model: {e}")

# Check database connection
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

print("\n🎯 Django version check completed!")
