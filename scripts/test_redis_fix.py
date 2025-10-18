#!/usr/bin/env python3
"""
Script para probar la conexión de Redis después de los cambios de configuración.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

django.setup()

def test_redis_connection():
    """Probar la conexión de Redis con la nueva configuración."""
    print("🔍 Probando conexión de Redis...")
    
    try:
        # Probar el cliente de Redis directo
        from utils.redis_cache import _r
        if _r:
            _r.ping()
            print("✅ Conexión directa a Redis exitosa")
        else:
            print("⚠️  Cliente de Redis no disponible")
            
    except Exception as e:
        print(f"❌ Error en conexión directa: {e}")
    
    try:
        # Probar el caché de Django
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 60)
        result = cache.get('test_key')
        if result == 'test_value':
            print("✅ Caché de Django funcionando correctamente")
        else:
            print("❌ Caché de Django no funciona correctamente")
            
    except Exception as e:
        print(f"❌ Error en caché de Django: {e}")
    
    try:
        # Probar funciones específicas de embeddings
        from utils.redis_cache import set_emb, get_emb
        test_text = "test embedding text"
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        set_emb(test_text, test_vector, 60)
        retrieved_vector = get_emb(test_text)
        
        if retrieved_vector == test_vector:
            print("✅ Funciones de embeddings funcionando correctamente")
        else:
            print("❌ Funciones de embeddings no funcionan correctamente")
            
    except Exception as e:
        print(f"❌ Error en funciones de embeddings: {e}")

def test_whatsapp_context():
    """Probar el contexto del WhatsApp Bot."""
    print("\n🔍 Probando contexto del WhatsApp Bot...")
    
    try:
        from apps.whatsapp_bot.services import LoggingService
        service = LoggingService()
        
        # Probar guardar contexto
        phone_number = "1234567890"
        context_data = {"test": "data", "step": "testing"}
        service.save_context(phone_number, context_data)
        
        # Probar recuperar contexto
        retrieved_context = service.get_context(phone_number)
        
        if retrieved_context and retrieved_context.get("test") == "data":
            print("✅ Contexto del WhatsApp Bot funcionando correctamente")
        else:
            print("❌ Contexto del WhatsApp Bot no funciona correctamente")
            
    except Exception as e:
        print(f"❌ Error en contexto del WhatsApp Bot: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de Redis...")
    test_redis_connection()
    test_whatsapp_context()
    print("\n✅ Pruebas completadas")
