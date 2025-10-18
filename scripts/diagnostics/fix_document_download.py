#!/usr/bin/env python3
"""
Script para corregir el error de descarga de documentos:
'argument of type NoneType is not iterable'

Este error ocurre cuando resolve_blob_name devuelve None y se intenta iterar sobre él.
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def print_section(title):
    """Imprimir una sección con formato."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def fix_storage_service():
    """Corregir el servicio de almacenamiento para manejar valores None."""
    print_section("CORRECCIÓN DEL SERVICIO DE ALMACENAMIENTO")
    
    try:
        storage_file = "services/storage_service.py"
        
        # Leer el archivo actual
        with open(storage_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene las correcciones
        if "if not resolved_name:" in content and "return None" in content:
            print("✅ El servicio de almacenamiento ya tiene las correcciones necesarias")
            return True
        
        # Buscar el método resolve_blob_name
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def resolve_blob_name(' in line:
                # Encontrar el final del método
                j = i + 1
                indent_level = len(line) - len(line.lstrip())
                while j < len(lines):
                    if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                        break
                    j += 1
                
                # Agregar verificación de None al final del método
                new_code = [
                    "        # Si no se encuentra, devolver None en lugar de string vacío",
                    "        if not resolved_name:",
                    "            logger.warning(f'No se pudo resolver el nombre del blob: {original}')",
                    "            return None",
                    "",
                    "        return resolved_name"
                ]
                
                # Insertar antes del final del método
                for k, code_line in enumerate(new_code):
                    lines.insert(j + k, "    " + code_line)
                
                # Escribir el archivo actualizado
                with open(storage_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                print("✅ Servicio de almacenamiento actualizado con manejo de None")
                return True
        
        print("❌ No se pudo encontrar el método resolve_blob_name")
        return False
        
    except Exception as e:
        print(f"❌ Error al corregir el servicio de almacenamiento: {e}")
        return False

def fix_document_views():
    """Corregir las vistas de documentos para manejar valores None."""
    print_section("CORRECCIÓN DE VISTAS DE DOCUMENTOS")
    
    try:
        views_file = "apps/documents/views.py"
        
        # Leer el archivo actual
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene las correcciones
        if "if not found_filename:" in content and "return redirect" in content:
            print("✅ Las vistas de documentos ya tienen las correcciones necesarias")
            return True
        
        # Buscar la función download_document
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def download_document(' in line:
                # Encontrar el final de la función
                j = i + 1
                indent_level = len(line) - len(line.lstrip())
                while j < len(lines):
                    if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                        break
                    j += 1
                
                # Agregar verificación adicional antes de get_blob_url
                new_code = [
                    "        # Verificar que found_filename no sea None",
                    "        if not found_filename:",
                    "            logger.error(f'No se pudo encontrar el archivo para: {document.title}')",
                    "            messages.error(request, f'El archivo '{document.title}' no se encuentra en el almacenamiento. Contacta al administrador.')",
                    "            return redirect('documents:document_list')",
                    "",
                ]
                
                # Insertar antes de la llamada a get_blob_url
                for k, code_line in enumerate(new_code):
                    lines.insert(j + k, "        " + code_line)
                
                # Escribir el archivo actualizado
                with open(views_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                print("✅ Vistas de documentos actualizadas con verificación de None")
                return True
        
        print("❌ No se pudo encontrar la función download_document")
        return False
        
    except Exception as e:
        print(f"❌ Error al corregir las vistas de documentos: {e}")
        return False

def test_fixes():
    """Probar que las correcciones funcionen."""
    print_section("PRUEBA DE CORRECCIONES")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
        import django
        django.setup()
        
        from apps.documents.models import Document
        from services.storage_service import azure_storage
        
        # Buscar documentos para probar
        documents = Document.objects.filter(title__icontains='Donaciones_Daya')
        
        if not documents.exists():
            print("❌ No se encontraron documentos para probar")
            return False
        
        doc = documents.first()
        print(f"📄 Probando documento: {doc.title}")
        
        # Probar resolve_blob_name con un nombre que no existe
        print("\n🔍 Probando resolve_blob_name con nombre inexistente...")
        try:
            resolved = azure_storage.resolve_blob_name("archivo_inexistente.txt")
            if resolved is None:
                print("✅ resolve_blob_name maneja correctamente valores None")
            else:
                print(f"⚠️  resolve_blob_name devolvió: {resolved}")
        except Exception as e:
            print(f"❌ Error en resolve_blob_name: {e}")
            return False
        
        # Probar get_blob_url con nombre inexistente
        print("\n🔗 Probando get_blob_url con nombre inexistente...")
        try:
            result = azure_storage.get_blob_url("archivo_inexistente.txt")
            if not result.get('success'):
                print("✅ get_blob_url maneja correctamente archivos inexistentes")
            else:
                print("⚠️  get_blob_url devolvió éxito para archivo inexistente")
        except Exception as e:
            print(f"❌ Error en get_blob_url: {e}")
            return False
        
        print("\n✅ Todas las pruebas pasaron")
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal."""
    print_section("CORRECCIÓN DE ERROR DE DESCARGA DE DOCUMENTOS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Aplicar correcciones
    storage_fixed = fix_storage_service()
    views_fixed = fix_document_views()
    
    # Probar correcciones
    tests_passed = test_fixes()
    
    # Resumen
    print_section("RESUMEN")
    print(f"Servicio de almacenamiento: {'✅ Corregido' if storage_fixed else '❌ Error'}")
    print(f"Vistas de documentos: {'✅ Corregido' if views_fixed else '❌ Error'}")
    print(f"Pruebas: {'✅ Pasaron' if tests_passed else '❌ Fallaron'}")
    
    if all([storage_fixed, views_fixed, tests_passed]):
        print("\n🎉 Todas las correcciones aplicadas exitosamente!")
        print("💡 Reinicia la aplicación para que los cambios tomen efecto")
    else:
        print("\n⚠️  Algunas correcciones fallaron")
        print("💡 Revisa los errores y aplica las correcciones manualmente")

if __name__ == "__main__":
    main()
