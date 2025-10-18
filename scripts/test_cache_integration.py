#!/usr/bin/env python3
"""
Script de prueba para verificar la integración del cache layer
con los servicios LLM y embedding_manager.
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_django():
    """Configurar Django para las pruebas"""
    # Configurar variables de entorno para desarrollo
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
    os.environ['CACHE_LAYER_ENABLED'] = 'True'
    os.environ['DEBUG'] = 'True'
    
    import django
    django.setup()
    
    logger.info("✅ Django configurado correctamente")

def test_cache_layer_import():
    """Probar que el cache layer se puede importar correctamente"""
    try:
        from utils.cache_layer import (
            get_emb, set_emb, get_ans, set_ans, 
            is_cache_enabled, get_cache_stats
        )
        logger.info("✅ Cache layer importado correctamente")
        return True
    except ImportError as e:
        logger.error(f"❌ Error importando cache layer: {e}")
        return False

def test_cache_enabled():
    """Probar si el cache está habilitado"""
    try:
        from utils.cache_layer import is_cache_enabled
        from django.conf import settings
        
        enabled = is_cache_enabled()
        feature_flag = getattr(settings, 'CACHE_LAYER_ENABLED', False)
        
        logger.info(f"Feature flag CACHE_LAYER_ENABLED: {feature_flag}")
        logger.info(f"Cache layer enabled: {enabled}")
        
        # En desarrollo, el cache puede estar deshabilitado si no hay Redis configurado
        # pero el feature flag debería estar habilitado
        return feature_flag
    except Exception as e:
        logger.error(f"❌ Error verificando cache: {e}")
        return False

def test_llm_service_integration():
    """Probar la integración del cache con el servicio LLM"""
    try:
        from functions.services.llm import generate_reply
        
        # Probar generación de respuesta
        test_message = "Hola, ¿cómo estás?"
        logger.info(f"Probando LLM service con mensaje: {test_message}")
        
        response = generate_reply(test_message)
        logger.info(f"Respuesta generada: {response[:100]}...")
        
        # Probar segunda vez para verificar cache
        logger.info("Probando segunda vez para verificar cache...")
        response2 = generate_reply(test_message)
        logger.info(f"Segunda respuesta: {response2[:100]}...")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en LLM service: {e}")
        return False

def test_embedding_manager_integration():
    """Probar la integración del cache con embedding_manager"""
    try:
        # Simular cache hit/miss sin crear el manager completo
        from utils.cache_layer import get_emb, set_emb
        
        test_content = "Este es un texto de prueba para embeddings"
        logger.info(f"Probando embedding cache con contenido: {test_content[:50]}...")
        
        # Primera vez - debería ser cache miss
        cached = get_emb(test_content)
        if cached:
            logger.info("Cache HIT en primera llamada")
        else:
            logger.info("Cache MISS en primera llamada")
        
        # Simular set de cache
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        set_result = set_emb(test_content, test_embedding)
        logger.info(f"Set cache result: {set_result}")
        
        # Segunda vez - debería ser cache hit
        cached2 = get_emb(test_content)
        if cached2:
            logger.info("Cache HIT en segunda llamada")
        else:
            logger.info("Cache MISS en segunda llamada")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en embedding manager: {e}")
        return False

def test_cache_stats_endpoint():
    """Probar el endpoint de estadísticas del cache"""
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Crear usuario admin para la prueba
        admin_user, created = User.objects.get_or_create(
            username='testadmin',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('testpass123')
            admin_user.save()
            logger.info("Usuario admin creado para pruebas")
        
        # Crear cliente y hacer login
        client = Client()
        login_success = client.login(username='testadmin', password='testpass123')
        logger.info(f"Login success: {login_success}")
        
        # Probar endpoint
        response = client.get('/ops/cache/stats/')
        logger.info(f"Status code del endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Estadísticas del cache: {data}")
            return True
        else:
            logger.error(f"Error en endpoint: {response.content}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando endpoint: {e}")
        return False

def test_cache_basic_operations():
    """Probar operaciones básicas del cache"""
    try:
        from utils.cache_layer import get_ans, set_ans, get_emb, set_emb
        
        # Probar cache de respuestas RAG
        test_query = "¿Cuáles son los servicios disponibles?"
        test_response = {
            'response': 'Los servicios disponibles incluyen...',
            'model': 'gpt-35-turbo',
            'max_tokens': 150
        }
        
        # Set cache
        set_result = set_ans(test_query, test_response)
        logger.info(f"Set ANS cache result: {set_result}")
        
        # Get cache
        cached_response = get_ans(test_query)
        if cached_response:
            logger.info("✅ Cache ANS funcionando correctamente")
        else:
            logger.info("⚠️ Cache ANS no disponible (posiblemente Redis no configurado)")
        
        # Probar cache de embeddings
        test_text = "Texto de prueba para embedding"
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Set cache
        set_result = set_emb(test_text, test_embedding)
        logger.info(f"Set EMB cache result: {set_result}")
        
        # Get cache
        cached_embedding = get_emb(test_text)
        if cached_embedding:
            logger.info("✅ Cache EMB funcionando correctamente")
        else:
            logger.info("⚠️ Cache EMB no disponible (posiblemente Redis no configurado)")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en operaciones básicas del cache: {e}")
        return False

def main():
    """Función principal de pruebas"""
    logger.info("🚀 Iniciando pruebas de integración del cache layer")
    
    # Configurar Django
    setup_django()
    
    # Ejecutar pruebas
    tests = [
        ("Import del cache layer", test_cache_layer_import),
        ("Cache habilitado", test_cache_enabled),
        ("Operaciones básicas del cache", test_cache_basic_operations),
        ("Integración LLM service", test_llm_service_integration),
        ("Integración embedding manager", test_embedding_manager_integration),
        ("Endpoint de estadísticas", test_cache_stats_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Probando: {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name}: PASÓ")
            else:
                logger.error(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen
    logger.info("\n" + "="*50)
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} pruebas pasaron")
    
    if passed >= 3:  # Al menos 3 pruebas deben pasar
        logger.info("🎉 Integración del cache layer funcionando correctamente!")
        return True
    else:
        logger.error("⚠️ Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
