#!/usr/bin/env python3
"""
Script para validar la configuración de SECRET_KEY en Django.
Uso: python scripts/validate_secret_key.py
"""

import os
import sys

def validate_secret_key():
    """Valida que la SECRET_KEY esté configurada correctamente"""
    
    print("🔍 Validando configuración de SECRET_KEY...")
    print("=" * 50)
    
    # Verificar variable de entorno
    secret_key = os.environ.get('SECRET_KEY')
    
    if not secret_key:
        print("❌ ERROR: SECRET_KEY no está configurada en las variables de entorno")
        print()
        print("Para solucionar esto:")
        print("1. En desarrollo: crea un archivo .env con SECRET_KEY=<tu-clave>")
        print("2. En producción: configura la variable de entorno SECRET_KEY")
        print("3. Ejecuta: python scripts/generate_secret_key.py para generar una nueva clave")
        return False
    
    # Verificar que no sea la clave por defecto
    default_keys = [
        "dev-secret-key-unsafe",
        "django-insecure-dev-secret-key-change-in-production",
        "your-secret-key-here",
        "test-secret-key-for-testing-only"
    ]
    
    if secret_key in default_keys:
        print("❌ ERROR: SECRET_KEY está usando un valor por defecto inseguro")
        print(f"   Clave actual: {'SET' if secret_key else 'NOT SET'}")
        print()
        print("Para solucionar esto:")
        print("1. Ejecuta: python scripts/generate_secret_key.py")
        print("2. Usa la clave generada en tu configuración")
        return False
    
    # Verificar longitud mínima
    if len(secret_key) < 50:
        print("❌ ERROR: SECRET_KEY es demasiado corta")
        print(f"   Longitud actual: {'VALID' if len(secret_key) >= 50 else 'INVALID'}")
        print("   Recomendación: SECRET_KEY debe tener al menos 50 caracteres")
        return False
    
    print("✅ SECRET_KEY configurada correctamente")
    print(f"   Longitud: {'VALID' if len(secret_key) >= 50 else 'INVALID'}")
    print(f"   Estado: {'SET' if secret_key else 'NOT SET'}")
    print()
    print("🔒 La clave parece ser segura y está configurada correctamente")
    
    return True

if __name__ == "__main__":
    success = validate_secret_key()
    sys.exit(0 if success else 1)
