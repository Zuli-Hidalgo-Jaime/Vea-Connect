#!/usr/bin/env python3
"""
Script de prueba para verificar el saneamiento de logs y protección de PII
"""

import os
import sys
import logging
import tempfile
from pathlib import Path
from contextlib import contextmanager
from io import StringIO

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup local environment
try:
    from scripts.setup_local_env import setup_local_environment
    setup_local_environment()
except ImportError:
    pass

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

import django
django.setup()

from utils.logging_extras import safe_value, get_safe_logger, safe_dict

@contextmanager
def captured_logs():
    """Capture logs for testing"""
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # Get root logger and add handler
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    
    try:
        yield log_capture
    finally:
        root_logger.removeHandler(handler)

def test_safe_value_function():
    """Prueba la función safe_value con diferentes tipos de datos sensibles"""
    print("🧪 Probando función safe_value...")
    
    test_cases = [
        # Datos sensibles que deben ser redactados
        ("sk-1234567890abcdef", "[REDACTED]"),
        ("password123", "[REDACTED]"),
        ("user@example.com", "[REDACTED]"),
        ("+1234567890", "[REDACTED]"),
        ("192.168.1.1", "[REDACTED]"),
        ("DefaultEndpointsProtocol=https;AccountName=test;AccountKey=secret", "[REDACTED]"),
        
        # Datos no sensibles que deben mantenerse
        ("document_123", "document_123"),
        ("user_id_456", "user_id_456"),
        ("status_success", "status_success"),
        ("", ""),
        (None, "None"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for input_value, expected in test_cases:
        result = safe_value(input_value)
        if result == expected:
            print(f"  ✅ {input_value} -> {result}")
            passed += 1
        else:
            print(f"  ❌ {input_value} -> {result} (esperado: {expected})")
    
    print(f"📊 Resultado: {passed}/{total} pruebas pasaron")
    return passed == total

def test_safe_logger():
    """Prueba el logger seguro"""
    print("\n🧪 Probando logger seguro...")
    
    # Crear logger seguro
    safe_logger = get_safe_logger("test_sanitization")
    
    # Capturar logs
    with captured_logs() as logs:
        # Loggear datos sensibles
        safe_logger.info("Processing user: %s", "user@example.com")
        safe_logger.info("API key: %s", "sk-1234567890abcdef")
        safe_logger.info("Password: %s", "secretpassword")
        
        # Loggear datos normales
        safe_logger.info("Document processed: %s", "document_123")
        safe_logger.info("Status: %s", "success")
    
    log_content = logs.getvalue()
    
    # Verificar que los datos sensibles fueron redactados
    sensitive_redacted = all([
        "[REDACTED]" in log_content,
        "user@example.com" not in log_content,
        "sk-1234567890abcdef" not in log_content,
        "secretpassword" not in log_content,
    ])
    
    # Verificar que los datos normales se mantuvieron
    normal_preserved = all([
        "document_123" in log_content,
        "success" in log_content,
    ])
    
    if sensitive_redacted and normal_preserved:
        print("  ✅ Logger seguro funciona correctamente")
        print("  ✅ Datos sensibles redactados")
        print("  ✅ Datos normales preservados")
        return True
    else:
        print("  ❌ Logger seguro no funciona correctamente")
        print(f"  Log content: {log_content}")
        return False

def test_safe_dict():
    """Prueba la función safe_dict con diccionarios"""
    print("\n🧪 Probando función safe_dict...")
    
    test_data = {
        "user_id": "12345",
        "email": "user@example.com",
        "api_key": "sk-1234567890abcdef",
        "password": "secret123",
        "status": "active",
        "nested": {
            "secret_token": "abc123def456",
            "normal_field": "normal_value"
        }
    }
    
    sanitized = safe_dict(test_data)
    
    # Verificar que los datos sensibles fueron redactados
    # Nota: las claves también pueden ser redactadas, así que verificamos los valores
    sensitive_redacted = all([
        "[REDACTED]" in str(sanitized.get("email", "")),
        "[REDACTED]" in str(sanitized.get("api_key", "")),
        "[REDACTED]" in str(sanitized.get("password", "")),
        "[REDACTED]" in str(sanitized.get("nested", {}).get("secret_token", "")),
    ])
    
    # Verificar que los datos normales se mantuvieron
    normal_preserved = all([
        "12345" in str(sanitized.get("user_id", "")),
        "active" in str(sanitized.get("status", "")),
        "normal_value" in str(sanitized.get("nested", {}).get("normal_field", "")),
    ])
    
    if sensitive_redacted and normal_preserved:
        print("  ✅ safe_dict funciona correctamente")
        return True
    else:
        print("  ❌ safe_dict no funciona correctamente")
        print(f"  Sanitized: {sanitized}")
        return False

def test_observability_preserved():
    """Prueba que la observabilidad se mantiene"""
    print("\n🧪 Probando preservación de observabilidad...")
    
    with captured_logs() as logs:
        safe_logger = get_safe_logger("test_observability")
        
        # Simular operaciones típicas de la aplicación
        safe_logger.info("Starting document processing")
        safe_logger.info("Processing document: %s", "document_123.pdf")
        safe_logger.info("Document size: %d bytes", 1024000)
        safe_logger.info("Processing completed successfully")
        safe_logger.warning("High memory usage detected: %d%%", 85)
        safe_logger.error("Failed to connect to database")
    
    log_content = logs.getvalue()
    
    # Verificar que la información útil se mantiene
    useful_info_preserved = all([
        "Starting document processing" in log_content,
        "document_123.pdf" in log_content,
        "1024000 bytes" in log_content,
        "Processing completed successfully" in log_content,
        "High memory usage detected: 85%" in log_content,
        "Failed to connect to database" in log_content,
    ])
    
    if useful_info_preserved:
        print("  ✅ Observabilidad preservada")
        print("  ✅ Información útil mantenida")
        return True
    else:
        print("  ❌ Observabilidad comprometida")
        print(f"  Log content: {log_content}")
        return False

def test_configuration_sanitization():
    """Prueba el saneamiento de configuración"""
    print("\n🧪 Probando saneamiento de configuración...")
    
    # Simular configuración típica
    config_data = {
        "database": {
            "host": "db.example.com",
            "user": "dbuser",
            "password": "secretpassword",
            "port": 5432
        },
        "azure": {
            "connection_string": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=secret",
            "api_key": "sk-1234567890abcdef"
        },
        "app": {
            "name": "VeaConnect",
            "version": "1.0.0",
            "debug": True
        }
    }
    
    sanitized = safe_dict(config_data)
    
    # Verificar que las credenciales fueron redactadas
    credentials_redacted = all([
        "[REDACTED]" in str(sanitized.get("database", {}).get("password", "")),
        "[REDACTED]" in str(sanitized.get("azure", {}).get("connection_string", "")),
        "[REDACTED]" in str(sanitized.get("azure", {}).get("api_key", "")),
    ])
    
    # Verificar que la información no sensible se mantiene
    info_preserved = all([
        "db.example.com" in str(sanitized.get("database", {}).get("host", "")),
        "dbuser" in str(sanitized.get("database", {}).get("user", "")),
        5432 == sanitized.get("database", {}).get("port", 0),
        "VeaConnect" in str(sanitized.get("app", {}).get("name", "")),
        "1.0.0" in str(sanitized.get("app", {}).get("version", "")),
        sanitized.get("app", {}).get("debug") is True,
    ])
    
    if credentials_redacted and info_preserved:
        print("  ✅ Configuración sanitizada correctamente")
        return True
    else:
        print("  ❌ Configuración no sanitizada correctamente")
        print(f"  Sanitized: {sanitized}")
        return False

def main():
    """Función principal de pruebas"""
    print("🔒 PRUEBAS DE SANEAMIENTO DE LOGS Y PROTECCIÓN DE PII")
    print("=" * 60)
    
    tests = [
        ("Función safe_value", test_safe_value_function),
        ("Logger seguro", test_safe_logger),
        ("Función safe_dict", test_safe_dict),
        ("Preservación de observabilidad", test_observability_preserved),
        ("Saneamiento de configuración", test_configuration_sanitization),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
        print("✅ El saneamiento de logs funciona correctamente")
        print("✅ La observabilidad se mantiene")
        print("✅ La protección de PII está activa")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores arriba")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
