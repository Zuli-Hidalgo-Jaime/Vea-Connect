#!/usr/bin/env python3
"""
Script para verificar el estado de la aplicación Django
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

try:
    django.setup()
    print("✅ Django configurado correctamente")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

try:
    from django.core.management import execute_from_command_line
    print("✅ Django management disponible")
except Exception as e:
    print(f"❌ Error con Django management: {e}")

try:
    from django.contrib.auth.models import User
    print("✅ Modelos de autenticación disponibles")
except Exception as e:
    print(f"❌ Error con modelos de autenticación: {e}")

try:
    from django.urls import reverse
    print("✅ Sistema de URLs disponible")
except Exception as e:
    print(f"❌ Error con sistema de URLs: {e}")

try:
    from django.template.loader import get_template
    template = get_template('core/login.html')
    print("✅ Template de login disponible")
except Exception as e:
    print(f"❌ Error con template de login: {e}")

print("\n🔍 Verificando configuración...")
print(f"DEBUG: {os.environ.get('DEBUG', 'No definido')}")
print(f"ALLOWED_HOSTS: {os.environ.get('ALLOWED_HOSTS', 'No definido')}")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'No definido')}")

print("\n✅ Verificación completada") 