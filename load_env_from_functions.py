#!/usr/bin/env python3
"""
Script para cargar variables de entorno desde functions/local.settings.json
"""
import json
import os
from pathlib import Path

def load_env_from_functions():
    """Carga variables de entorno desde functions/local.settings.json"""
    functions_settings_path = Path(__file__).parent / "functions" / "local.settings.json"
    
    if not functions_settings_path.exists():
        print(f"❌ No se encontró el archivo: {functions_settings_path}")
        return False
    
    try:
        with open(functions_settings_path, 'r') as f:
            settings = json.load(f)
        
        # Cargar variables desde Values
        values = settings.get('Values', {})
        
        # Variables críticas que necesitamos
        critical_vars = [
            'AZURE_STORAGE_CONNECTION_STRING',
            'AZURE_STORAGE_ACCOUNT_NAME', 
            'AZURE_STORAGE_ACCOUNT_KEY',
            'AZURE_STORAGE_CONTAINER_NAME',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_CHAT_DEPLOYMENT',
            'AZURE_OPENAI_CHAT_API_VERSION',
            'AZURE_SEARCH_ENDPOINT',
            'AZURE_SEARCH_KEY',  # Nota: en local.settings.json está como AZURE_SEARCH_KEY
            'AZURE_SEARCH_INDEX_NAME',
            'ACS_WHATSAPP_ENDPOINT',
            'ACS_WHATSAPP_API_KEY',
            'ACS_PHONE_NUMBER',
            'WHATSAPP_CHANNEL_ID_GUID',
            'AZURE_REDIS_CONNECTIONSTRING',
            'VISION_ENDPOINT',
            'VISION_KEY',
            'SECRET_KEY'
        ]
        
        loaded_count = 0
        for var in critical_vars:
            value = values.get(var)
            if value:
                os.environ[var] = value
                loaded_count += 1
                print(f"✅ Cargada: {var}")
            else:
                print(f"❌ No encontrada: {var}")
        
        print(f"\n📊 Variables cargadas: {loaded_count}/{len(critical_vars)}")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando variables: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Cargando variables de entorno desde functions/local.settings.json...")
    success = load_env_from_functions()
    if success:
        print("✅ Variables cargadas exitosamente")
    else:
        print("❌ Error al cargar variables")
