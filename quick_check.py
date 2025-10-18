#!/usr/bin/env python3
"""
Verificación rápida de configuración
"""

import os
import sys
import django

print("=== VERIFICACIÓN RÁPIDA ===")

# Verificar versión de Django
print(f"Django version: {django.get_version()}")

# Verificar variables críticas
critical_vars = [
    'AZURE_POSTGRESQL_NAME',
    'AZURE_POSTGRESQL_USERNAME', 
    'AZURE_POSTGRESQL_PASSWORD',
    'AZURE_POSTGRESQL_HOST'
]

print("\nVariables críticas:")
for var in critical_vars:
    value = os.environ.get(var)
    if value:
        print(f"✅ {var}: CONFIGURADA")
    else:
        print(f"❌ {var}: NO CONFIGURADA")

# Verificar archivo de configuración
config_file = "config/settings/azure_production.py"
if os.path.exists(config_file):
    print(f"✅ {config_file}: EXISTE")
else:
    print(f"❌ {config_file}: NO EXISTE")

print("\n=== FIN VERIFICACIÓN ===")
