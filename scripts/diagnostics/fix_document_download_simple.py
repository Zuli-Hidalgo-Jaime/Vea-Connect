#!/usr/bin/env python3
"""
Script simplificado para corregir el error de descarga de documentos:
'argument of type NoneType is not iterable'

Este error ocurre cuando resolve_blob_name devuelve None y se intenta iterar sobre él.
Versión compatible con Windows.
"""

import os
import sys
from datetime import datetime

def print_section(title):
    """Imprimir una sección con formato."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def fix_storage_service():
    """Corregir el servicio de almacenamiento para manejar valores None."""
    print_section("CORRECCION DEL SERVICIO DE ALMACENAMIENTO")
    
    try:
        storage_file = "services/storage_service.py"
        
        if not os.path.exists(storage_file):
            print("ERROR: No se encuentra el archivo de servicio de almacenamiento")
            return False
        
        # Leer el archivo actual
        with open(storage_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene las correcciones
        if "if not resolved_name:" in content and "return None" in content:
            print("OK: El servicio de almacenamiento ya tiene las correcciones necesarias")
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
                
                print("OK: Servicio de almacenamiento actualizado con manejo de None")
                return True
        
        print("ERROR: No se pudo encontrar el metodo resolve_blob_name")
        return False
        
    except Exception as e:
        print(f"ERROR al corregir el servicio de almacenamiento: {e}")
        return False

def fix_document_views():
    """Corregir las vistas de documentos para manejar valores None."""
    print_section("CORRECCION DE VISTAS DE DOCUMENTOS")
    
    try:
        views_file = "apps/documents/views.py"
        
        if not os.path.exists(views_file):
            print("ERROR: No se encuentra el archivo de vistas")
            return False
        
        # Leer el archivo actual
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene las correcciones
        if "if not found_filename:" in content and "return redirect" in content:
            print("OK: Las vistas de documentos ya tienen las correcciones necesarias")
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
                
                print("OK: Vistas de documentos actualizadas con verificacion de None")
                return True
        
        print("ERROR: No se pudo encontrar la funcion download_document")
        return False
        
    except Exception as e:
        print(f"ERROR al corregir las vistas de documentos: {e}")
        return False

def verify_fixes():
    """Verificar que las correcciones se aplicaron correctamente."""
    print_section("VERIFICACION DE CORRECCIONES")
    
    try:
        # Verificar archivo de servicio
        storage_file = "services/storage_service.py"
        if os.path.exists(storage_file):
            with open(storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "if not resolved_name:" in content and "return None" in content:
                print("OK: Servicio de almacenamiento corregido")
            else:
                print("ADVERTENCIA: Servicio de almacenamiento no tiene las correcciones")
        
        # Verificar archivo de vistas
        views_file = "apps/documents/views.py"
        if os.path.exists(views_file):
            with open(views_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "if not found_filename:" in content:
                print("OK: Vistas de documentos corregidas")
            else:
                print("ADVERTENCIA: Vistas de documentos no tienen las correcciones")
        
        return True
        
    except Exception as e:
        print(f"ERROR durante la verificacion: {e}")
        return False

def main():
    """Función principal."""
    print_section("CORRECCION DE ERROR DE DESCARGA DE DOCUMENTOS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Aplicar correcciones
    storage_fixed = fix_storage_service()
    views_fixed = fix_document_views()
    
    # Verificar correcciones
    verification_ok = verify_fixes()
    
    # Resumen
    print_section("RESUMEN")
    print(f"Servicio de almacenamiento: {'Corregido' if storage_fixed else 'Error'}")
    print(f"Vistas de documentos: {'Corregido' if views_fixed else 'Error'}")
    print(f"Verificacion: {'OK' if verification_ok else 'Error'}")
    
    if all([storage_fixed, views_fixed, verification_ok]):
        print("\nTODAS LAS CORRECCIONES APLICADAS EXITOSAMENTE!")
        print("Reinicia la aplicacion para que los cambios tomen efecto")
    else:
        print("\nAlgunas correcciones fallaron")
        print("Revisa los errores y aplica las correcciones manualmente")

if __name__ == "__main__":
    main()
