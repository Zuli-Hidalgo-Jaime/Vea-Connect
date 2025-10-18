#!/usr/bin/env python3
"""
Script para verificar variables de entorno
"""
import os

# Variables críticas para verificar
critical_vars = [
    'AZURE_STORAGE_CONNECTION_STRING',
    'AZURE_STORAGE_ACCOUNT_NAME', 
    'AZURE_STORAGE_ACCOUNT_KEY',
    'AZURE_STORAGE_CONTAINER_NAME',
    'AZURE_OPENAI_ENDPOINT',
    'AZURE_OPENAI_API_KEY',
    'AZURE_SEARCH_ENDPOINT',
    'AZURE_SEARCH_API_KEY',
    'AZURE_SEARCH_INDEX_NAME',
    'ACS_WHATSAPP_ENDPOINT',
    'ACS_WHATSAPP_API_KEY',
    'ACS_PHONE_NUMBER',
    'WHATSAPP_CHANNEL_ID_GUID',
    'AZURE_REDIS_CONNECTIONSTRING'
]

print("🔍 Verificando variables de entorno...")
print("=" * 50)

for var in critical_vars:
    value = os.environ.get(var)
    if value:
        # Mostrar solo los primeros 20 caracteres para seguridad
        display_value = value[:20] + "..." if len(value) > 20 else value
        print(f"✅ {var}: {display_value}")
    else:
        print(f"❌ {var}: NO CONFIGURADA")

print("\n" + "=" * 50)
print("📊 Resumen:")
configured = sum(1 for var in critical_vars if os.environ.get(var))
print(f"Variables configuradas: {configured}/{len(critical_vars)}")
print(f"Porcentaje: {(configured/len(critical_vars)*100):.1f}%")
