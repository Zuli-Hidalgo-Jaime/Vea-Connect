#!/usr/bin/env python3
"""
Script de prueba para verificar que la auditoría funciona correctamente
"""

import os
import sys
from pathlib import Path

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

from django.conf import settings
from apps.directory.models import Contact
from apps.documents.models import Document

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("🔍 Probando conexión a la base de datos...")
    
    try:
        # Verificar configuración de base de datos
        print(f"✓ Configuración de base de datos: {settings.DATABASES['default']['ENGINE']}")
        
        # Probar consulta simple
        contact_count = Contact.objects.count()
        print(f"✓ Contactos en la base de datos: {contact_count}")
        
        document_count = Document.objects.count()
        print(f"✓ Documentos en la base de datos: {document_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la conexión a la base de datos: {e}")
        return False

def test_contact_model():
    """Prueba el modelo Contact"""
    print("\n🔍 Probando modelo Contact...")
    
    try:
        # Verificar campos disponibles
        contact_fields = [field.name for field in Contact._meta.fields]
        print(f"✓ Campos del modelo Contact: {contact_fields}")
        
        # Verificar que no hay campo updated_at
        if 'updated_at' not in contact_fields:
            print("✓ Campo 'updated_at' no existe (correcto)")
        else:
            print("⚠️ Campo 'updated_at' existe (puede causar problemas)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando modelo Contact: {e}")
        return False

def test_audit_script():
    """Prueba el script de auditoría"""
    print("\n🔍 Probando script de auditoría...")
    
    try:
        from scripts.cleanup.orphans_audit import OrphanedDataAuditor
        
        # Crear auditor en modo dry-run
        auditor = OrphanedDataAuditor(dry_run=True, days_threshold=30, verbose=True)
        
        # Probar auditoría de contactos
        orphaned_contacts = auditor.audit_orphaned_contacts()
        print(f"✓ Auditoría de contactos completada: {len(orphaned_contacts)} contactos huérfanos encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando script de auditoría: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 Iniciando pruebas de auditoría...\n")
    
    tests = [
        ("Conexión a base de datos", test_database_connection),
        ("Modelo Contact", test_contact_model),
        ("Script de auditoría", test_audit_script),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"📋 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
        print()
    
    # Resumen de resultados
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El script de auditoría está funcionando correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()
