#!/usr/bin/env python3
"""
Diagnóstico completo del sistema VEA Connect
"""
import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_django_apps():
    """Verificar aplicaciones Django"""
    logger.info("🔍 Verificando aplicaciones Django...")
    
    apps_dir = Path("apps")
    if not apps_dir.exists():
        logger.error("❌ Directorio 'apps' no encontrado")
        return False
    
    # Verificar módulos vacíos
    empty_modules = []
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and app_dir.name != "__pycache__":
            init_file = app_dir / "__init__.py"
            if init_file.exists() and init_file.stat().st_size == 0:
                empty_modules.append(app_dir.name)
    
    if empty_modules:
        logger.warning(f"⚠️ Módulos vacíos encontrados: {empty_modules}")
    else:
        logger.info("✅ Todos los módulos tienen contenido")
    
    return True

def check_azure_functions():
    """Verificar Azure Functions"""
    logger.info("🔍 Verificando Azure Functions...")
    
    functions_dir = Path("functions")
    if not functions_dir.exists():
        logger.error("❌ Directorio 'functions' no encontrado")
        return False
    
    # Verificar archivo principal
    function_app = functions_dir / "function_app.py"
    if not function_app.exists():
        logger.error("❌ function_app.py no encontrado")
        return False
    else:
        logger.info("✅ function_app.py encontrado")
    
    # Verificar funciones individuales
    functions = [
        "whatsapp_event_grid_trigger",
        "health", 
        "create_embedding",
        "search_similar",
        "get_stats",
        "embeddings_health_check"
    ]
    
    missing_functions = []
    for func_name in functions:
        func_dir = functions_dir / func_name
        if not func_dir.exists():
            missing_functions.append(func_name)
        else:
            init_file = func_dir / "__init__.py"
            if not init_file.exists():
                missing_functions.append(f"{func_name}/__init__.py")
    
    if missing_functions:
        logger.error(f"❌ Funciones faltantes: {missing_functions}")
        return False
    else:
        logger.info("✅ Todas las funciones están presentes")
    
    return True

def check_whatsapp_bot():
    """Verificar bot de WhatsApp"""
    logger.info("🔍 Verificando bot de WhatsApp...")
    
    bot_dir = Path("apps/whatsapp_bot")
    if not bot_dir.exists():
        logger.error("❌ Directorio del bot de WhatsApp no encontrado")
        return False
    
    # Verificar archivos críticos
    critical_files = [
        "views.py",
        "handlers.py", 
        "models.py",
        "urls.py"
    ]
    
    missing_files = []
    for file_name in critical_files:
        file_path = bot_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        logger.error(f"❌ Archivos faltantes del bot: {missing_files}")
        return False
    else:
        logger.info("✅ Todos los archivos del bot están presentes")
    
    return True

def check_environment_variables():
    """Verificar variables de entorno críticas"""
    logger.info("🔍 Verificando variables de entorno...")
    
    critical_vars = [
        "AZURE_POSTGRESQL_NAME",
        "AZURE_POSTGRESQL_USERNAME", 
        "AZURE_POSTGRESQL_PASSWORD",
        "AZURE_POSTGRESQL_HOST",
        "AZURE_STORAGE_ACCOUNT_NAME",
        "AZURE_STORAGE_ACCOUNT_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "ACS_CONNECTION_STRING"
    ]
    
    missing_vars = []
    for var_name in critical_vars:
        if not os.environ.get(var_name):
            missing_vars.append(var_name)
    
    if missing_vars:
        logger.warning(f"⚠️ Variables de entorno faltantes: {missing_vars}")
    else:
        logger.info("✅ Todas las variables críticas están configuradas")
    
    return len(missing_vars) == 0

def check_imports():
    """Verificar importaciones críticas"""
    logger.info("🔍 Verificando importaciones...")
    
    try:
        import django
        logger.info("✅ Django importado correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando Django: {e}")
        return False
    
    try:
        from apps.whatsapp_bot.handlers import WhatsAppBotHandler
        logger.info("✅ WhatsAppBotHandler importado correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando WhatsAppBotHandler: {e}")
        return False
    
    try:
        import azure.functions
        logger.info("✅ Azure Functions importado correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando Azure Functions: {e}")
        return False
    
    return True

def main():
    """Ejecutar diagnóstico completo"""
    logger.info("🚀 Iniciando diagnóstico completo del sistema VEA Connect")
    logger.info("=" * 60)
    
    results = []
    
    # Ejecutar todas las verificaciones
    results.append(("Django Apps", check_django_apps()))
    results.append(("Azure Functions", check_azure_functions()))
    results.append(("WhatsApp Bot", check_whatsapp_bot()))
    results.append(("Environment Variables", check_environment_variables()))
    results.append(("Importaciones", check_imports()))
    
    # Resumen
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DEL DIAGNÓSTICO:")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"  {check_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 60)
    logger.info(f"🎯 Resultado: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        logger.info("🎉 ¡Sistema en buen estado!")
        return 0
    else:
        logger.error("⚠️ Se encontraron problemas que requieren atención")
        return 1

if __name__ == "__main__":
    sys.exit(main())
