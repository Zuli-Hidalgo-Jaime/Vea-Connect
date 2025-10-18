#!/usr/bin/env python3
"""
Script simple para verificar el código de documents sin cargar Django
"""

import os
import sys
from pathlib import Path

def check_imports():
    """Verificar que las importaciones funcionan"""
    print("=== VERIFICACIÓN DE IMPORTACIONES ===")
    
    # Agregar el directorio del proyecto al path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        # Verificar importaciones básicas
        print("1. Verificando importaciones básicas...")
        
        # Verificar que el archivo __init__.py existe
        init_file = project_root / "apps" / "documents" / "__init__.py"
        if init_file.exists():
            print("   ✓ apps/documents/__init__.py existe")
        else:
            print("   ❌ apps/documents/__init__.py no existe")
        
        # Verificar que apps.py existe
        apps_file = project_root / "apps" / "documents" / "apps.py"
        if apps_file.exists():
            print("   ✓ apps/documents/apps.py existe")
        else:
            print("   ❌ apps/documents/apps.py no existe")
        
        # Verificar que models.py existe
        models_file = project_root / "apps" / "documents" / "models.py"
        if models_file.exists():
            print("   ✓ apps/documents/models.py existe")
        else:
            print("   ❌ apps/documents/models.py no existe")
        
        # Verificar que views.py existe
        views_file = project_root / "apps" / "documents" / "views.py"
        if views_file.exists():
            print("   ✓ apps/documents/views.py existe")
        else:
            print("   ❌ apps/documents/views.py no existe")
        
        # Verificar que forms.py existe
        forms_file = project_root / "apps" / "documents" / "forms.py"
        if forms_file.exists():
            print("   ✓ apps/documents/forms.py existe")
        else:
            print("   ❌ apps/documents/forms.py no existe")
        
        # Verificar que urls.py existe
        urls_file = project_root / "apps" / "documents" / "urls.py"
        if urls_file.exists():
            print("   ✓ apps/documents/urls.py existe")
        else:
            print("   ❌ apps/documents/urls.py no existe")
        
        # Verificar que signals.py existe
        signals_file = project_root / "apps" / "documents" / "signals.py"
        if signals_file.exists():
            print("   ✓ apps/documents/signals.py existe")
        else:
            print("   ❌ apps/documents/signals.py no existe")
        
        # Verificar que utils.py existe
        utils_file = project_root / "apps" / "documents" / "utils.py"
        if utils_file.exists():
            print("   ✓ apps/documents/utils.py existe")
        else:
            print("   ❌ apps/documents/utils.py no existe")
        
        # Verificar directorio de templates
        templates_dir = project_root / "apps" / "documents" / "templates"
        if templates_dir.exists():
            print("   ✓ apps/documents/templates/ existe")
            
            # Verificar archivos de templates
            template_files = [
                "documents.html",
                "create.html",
                "documents/create.html",
                "documents/confirm_delete.html",
                "documents/download_error.html"
            ]
            
            for template_file in template_files:
                template_path = templates_dir / template_file
                if template_path.exists():
                    print(f"   ✓ Template {template_file} existe")
                else:
                    print(f"   ❌ Template {template_file} no existe")
        else:
            print("   ❌ apps/documents/templates/ no existe")
        
        # Verificar directorio de migrations
        migrations_dir = project_root / "apps" / "documents" / "migrations"
        if migrations_dir.exists():
            print("   ✓ apps/documents/migrations/ existe")
            
            # Verificar archivos de migración
            migration_files = list(migrations_dir.glob("*.py"))
            if migration_files:
                print(f"   ✓ {len(migration_files)} archivos de migración encontrados")
            else:
                print("   ⚠ No se encontraron archivos de migración")
        else:
            print("   ❌ apps/documents/migrations/ no existe")
        
    except Exception as e:
        print(f"   ❌ Error verificando archivos: {e}")

def check_syntax():
    """Verificar sintaxis de los archivos Python"""
    print("\n=== VERIFICACIÓN DE SINTAXIS ===")
    
    project_root = Path(__file__).resolve().parent.parent.parent
    
    python_files = [
        "apps/documents/__init__.py",
        "apps/documents/apps.py",
        "apps/documents/models.py",
        "apps/documents/views.py",
        "apps/documents/forms.py",
        "apps/documents/urls.py",
        "apps/documents/signals.py",
        "apps/documents/utils.py"
    ]
    
    for file_path in python_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Intentar compilar el código
                compile(content, str(full_path), 'exec')
                print(f"   ✓ {file_path} - Sintaxis correcta")
            except SyntaxError as e:
                print(f"   ❌ {file_path} - Error de sintaxis: {e}")
            except Exception as e:
                print(f"   ❌ {file_path} - Error: {e}")
        else:
            print(f"   ⚠ {file_path} - Archivo no encontrado")

def check_utilities():
    """Verificar archivos de utilidades"""
    print("\n=== VERIFICACIÓN DE UTILIDADES ===")
    
    project_root = Path(__file__).resolve().parent.parent.parent
    
    utility_files = [
        "utilities/azureblobstorage.py",
        "utilities/embedding_manager.py",
        "utilities/azure_search_client.py"
    ]
    
    for file_path in utility_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Intentar compilar el código
                compile(content, str(full_path), 'exec')
                print(f"   ✓ {file_path} - Sintaxis correcta")
            except SyntaxError as e:
                print(f"   ❌ {file_path} - Error de sintaxis: {e}")
            except Exception as e:
                print(f"   ❌ {file_path} - Error: {e}")
        else:
            print(f"   ⚠ {file_path} - Archivo no encontrado")

if __name__ == "__main__":
    check_imports()
    check_syntax()
    check_utilities()
    print("\n=== FIN DE LA VERIFICACIÓN ===")
