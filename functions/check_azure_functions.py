#!/usr/bin/env python3
"""
Script para verificar qué funciones están realmente desplegadas en Azure.
"""

import os
import json
import requests
import logging
from typing import Dict, Any, List

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_function_list():
    """Obtener la lista de funciones desde Azure."""
    logger.info("=== OBTENIENDO LISTA DE FUNCIONES DESDE AZURE ===")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return []
    
    try:
        # Intentar obtener la lista de funciones desde el endpoint de administración
        admin_url = f"{function_app_url}/admin/functions"
        logger.info(f"Consultando: {admin_url}")
        
        response = requests.get(admin_url, timeout=10)
        
        if response.status_code == 200:
            functions_data = response.json()
            logger.info(f"Funciones encontradas: {len(functions_data)}")
            
            for func in functions_data:
                func_name = func.get('name', 'Unknown')
                func_status = func.get('status', 'Unknown')
                logger.info(f"  - {func_name}: {func_status}")
            
            return functions_data
        else:
            logger.warning(f"No se pudo obtener lista de funciones: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error obteniendo lista de funciones: {e}")
        return []

def test_function_endpoints():
    """Probar endpoints específicos de funciones."""
    logger.info("\n=== PROBANDO ENDPOINTS ESPECÍFICOS ===")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return
    
    # Lista de endpoints a probar
    endpoints = [
        # Funciones HTTP
        ('health', '/api/health'),
        ('get_stats', '/api/get_stats'),
        ('create_embedding', '/api/create_embedding'),
        ('search_similar', '/api/search_similar'),
        ('embeddings_health_check', '/api/embeddings_health_check'),
        ('test_sdk_function', '/api/test_sdk_function'),
        
        # Rutas alternativas
        ('embeddings/health', '/api/embeddings/health'),
        ('embeddings/stats', '/api/embeddings/stats'),
        ('embeddings/create', '/api/embeddings/create'),
        ('embeddings/search', '/api/embeddings/search'),
        
        # Event Grid trigger (debería fallar con 405)
        ('whatsapp_event_grid_trigger', '/api/whatsapp_event_grid_trigger'),
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for name, path in endpoints:
        try:
            url = f"{function_app_url}{path}"
            logger.info(f"Probando: {name}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"  ✅ {name}: FUNCIONANDO (200)")
                working_endpoints.append(name)
            elif response.status_code == 405 and name == 'whatsapp_event_grid_trigger':
                logger.info(f"  ✅ {name}: DESPLEGADA (405 Method Not Allowed es esperado)")
                working_endpoints.append(name)
            else:
                logger.warning(f"  ❌ {name}: ERROR ({response.status_code})")
                failed_endpoints.append(name)
                
        except Exception as e:
            logger.error(f"  ❌ {name}: EXCEPCIÓN - {e}")
            failed_endpoints.append(name)
    
    logger.info(f"\nResumen:")
    logger.info(f"Endpoints funcionando: {len(working_endpoints)}")
    logger.info(f"Endpoints fallando: {len(failed_endpoints)}")
    
    if working_endpoints:
        logger.info(f"Funcionando: {', '.join(working_endpoints)}")
    if failed_endpoints:
        logger.info(f"Fallando: {', '.join(failed_endpoints)}")

def check_function_app_info():
    """Obtener información de la Function App."""
    logger.info("\n=== INFORMACIÓN DE LA FUNCTION APP ===")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return
    
    try:
        # Probar el endpoint de información de la función
        info_url = f"{function_app_url}/api/health"
        response = requests.get(info_url, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info("Información de la Function App:")
                logger.info(f"  Status: {data.get('status', 'Unknown')}")
                logger.info(f"  Message: {data.get('message', 'Unknown')}")
                
                functions = data.get('functions', [])
                if functions:
                    logger.info(f"  Funciones reportadas: {len(functions)}")
                    for func in functions[:10]:  # Mostrar solo las primeras 10
                        logger.info(f"    - {func}")
                    if len(functions) > 10:
                        logger.info(f"    ... y {len(functions) - 10} más")
                else:
                    logger.warning("  No se encontraron funciones en la respuesta")
                    
            except json.JSONDecodeError:
                logger.warning("  La respuesta no es JSON válido")
                logger.info(f"  Respuesta: {response.text[:200]}...")
        else:
            logger.warning(f"No se pudo obtener información: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error obteniendo información: {e}")

def main():
    """Función principal."""
    logger.info("Iniciando verificación de funciones en Azure...")
    
    # Cargar variables de entorno
    try:
        with open('local.settings.json', 'r') as f:
            local_settings = json.load(f)
            for key, value in local_settings.get('Values', {}).items():
                os.environ[key] = value
        logger.info("Variables de entorno cargadas")
    except Exception as e:
        logger.warning(f"No se pudo cargar local.settings.json: {e}")
    
    # Obtener información de la Function App
    check_function_app_info()
    
    # Obtener lista de funciones
    get_function_list()
    
    # Probar endpoints
    test_function_endpoints()
    
    logger.info("\n=== VERIFICACIÓN COMPLETADA ===")
    logger.info("Si no ves la función whatsapp_event_grid_trigger, verifica:")
    logger.info("1. Que el despliegue haya incluido todos los archivos")
    logger.info("2. Que no haya errores en los logs de despliegue")
    logger.info("3. Que las variables de entorno estén configuradas en Azure")

if __name__ == "__main__":
    main()
