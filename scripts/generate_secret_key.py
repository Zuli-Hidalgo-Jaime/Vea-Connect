#!/usr/bin/env python3
"""
Script para generar SECRET_KEYs seguras para Django.
Uso: python scripts/generate_secret_key.py
"""

import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from django.core.management.utils import get_random_secret_key
except ImportError:
    print("Error: Django no está instalado. Instala Django primero:")
    print("pip install django")
    sys.exit(1)

def generate_secret_key():
    """Genera una SECRET_KEY segura para Django"""
    secret_key = get_random_secret_key()
    
    print("=" * 60)
    print("SECRET_KEY generada para Django:")
    print("=" * 60)
    print(secret_key)
    print("=" * 60)
    print()
    print("Para usar esta SECRET_KEY:")
    print("1. En desarrollo local: agrega SECRET_KEY=<clave> a tu archivo .env")
    print("2. En producción: configura la variable de entorno SECRET_KEY")
    print("3. En GitHub Actions: agrega SECRET_KEY como secret en tu repositorio")
    print()
    print("⚠️  IMPORTANTE: Nunca compartas o commits esta clave en el código!")
    print("=" * 60)
    
    return secret_key

if __name__ == "__main__":
    generate_secret_key()
