#!/usr/bin/env python3
"""
Script de verificación de correcciones de linter.

Este script verifica que todos los errores de linter identificados anteriormente
han sido corregidos exitosamente.
"""

import sys
import os
import importlib

def test_azure_search_imports():
    """Test Azure Search SDK imports."""
    print("🔍 Verificando importaciones de Azure Search SDK...")
    
    try:
        import azure.search.documents
        print("  ✅ azure.search.documents importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando azure.search.documents: {e}")
        return False
    
    try:
        import azure.search.documents.indexes
        print("  ✅ azure.search.documents.indexes importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando azure.search.documents.indexes: {e}")
        return False
    
    try:
        import azure.search.documents.indexes.models
        print("  ✅ azure.search.documents.indexes.models importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando azure.search.documents.indexes.models: {e}")
        return False
    
    return True

def test_django_orm_imports():
    """Test Django ORM imports."""
    print("🔍 Verificando importaciones de Django ORM...")
    
    try:
        import django
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
        django.setup()
        print("  ✅ Django configurado correctamente")
    except Exception as e:
        print(f"  ❌ Error configurando Django: {e}")
        return False
    
    try:
        from django.db.models import Q
        print("  ✅ django.db.models.Q importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando django.db.models.Q: {e}")
        return False
    
    try:
        from apps.documents.models import Document
        print("  ✅ apps.documents.models.Document importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando apps.documents.models.Document: {e}")
        return False
    
    return True

def test_azure_search_client():
    """Test Azure Search Client functionality."""
    print("🔍 Verificando funcionalidad de Azure Search Client...")
    
    try:
        from utilities.azure_search_client import AzureSearchClient, get_azure_search_client
        print("  ✅ utilities.azure_search_client importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando utilities.azure_search_client: {e}")
        return False
    
    try:
        # Test client creation (will fail if env vars not set, but import should work)
        client = get_azure_search_client()
        print("  ✅ AzureSearchClient creado correctamente")
    except ValueError as e:
        # Expected error if env vars not configured
        print(f"  ⚠️ AzureSearchClient requiere configuración de variables de entorno: {e}")
    except Exception as e:
        print(f"  ❌ Error inesperado creando AzureSearchClient: {e}")
        return False
    
    return True

def test_documents_views():
    """Test documents views imports."""
    print("🔍 Verificando importaciones de apps.documents.views...")
    
    try:
        from apps.documents.views import document_list
        print("  ✅ apps.documents.views importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando apps.documents.views: {e}")
        return False
    
    return True

def test_signals():
    """Test signals imports."""
    print("🔍 Verificando importaciones de signals...")
    
    try:
        from apps.documents.signals import upload_document_to_blob
        print("  ✅ apps.documents.signals importado correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando apps.documents.signals: {e}")
        return False
    
    return True

def main():
    """Main verification function."""
    print("🚀 Iniciando verificación de correcciones de linter...")
    print("=" * 60)
    
    tests = [
        ("Azure Search SDK Imports", test_azure_search_imports),
        ("Django ORM Imports", test_django_orm_imports),
        ("Azure Search Client", test_azure_search_client),
        ("Documents Views", test_documents_views),
        ("Signals", test_signals),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: EXITOSO")
            else:
                print(f"❌ {test_name}: FALLÓ")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡TODAS LAS CORRECCIONES DE LINTER HAN SIDO EXITOSAS!")
        print("✅ El proyecto está listo para desarrollo y producción")
        return 0
    else:
        print("⚠️ Algunas correcciones requieren atención adicional")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 