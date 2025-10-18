#!/usr/bin/env python3
"""
Script para desplegar las correcciones de producción a Azure.
Este script aplica las correcciones localmente y prepara el despliegue.
"""

import os
import sys
import subprocess
from datetime import datetime

def print_section(title):
    """Imprimir una sección con formato."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_git_status():
    """Verificar el estado de Git."""
    print_section("VERIFICACION DE GIT")
    
    try:
        # Verificar si estamos en un repositorio Git
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: No se encuentra un repositorio Git")
            return False
        
        print("OK: Repositorio Git encontrado")
        
        # Verificar cambios pendientes
        result = subprocess.run(['git', 'diff', '--name-only'], capture_output=True, text=True)
        if result.stdout.strip():
            print("Cambios pendientes detectados:")
            for file in result.stdout.strip().split('\n'):
                if file:
                    print(f"  - {file}")
        else:
            print("No hay cambios pendientes")
        
        return True
        
    except Exception as e:
        print(f"ERROR al verificar Git: {e}")
        return False

def apply_fixes():
    """Aplicar las correcciones necesarias."""
    print_section("APLICACION DE CORRECCIONES")
    
    fixes_applied = []
    
    # 1. Verificar ALLOWED_HOSTS
    settings_file = "config/settings/azure_production.py"
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '169.254.130.4' not in content:
            print("ERROR: ALLOWED_HOSTS no incluye la IP 169.254.130.4")
            print("Aplicando correccion...")
            
            # Buscar la línea de ALLOWED_HOSTS y agregar la IP
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'ALLOWED_HOSTS = [' in line:
                    # Encontrar el final del array
                    j = i
                    while j < len(lines) and ']' not in lines[j]:
                        j += 1
                    
                    # Insertar la IP antes del cierre del array
                    lines.insert(j, "    '169.254.130.4',  # IP específica del error")
                    
                    # Escribir el archivo actualizado
                    with open(settings_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    print("OK: ALLOWED_HOSTS corregido")
                    fixes_applied.append("ALLOWED_HOSTS")
                    break
        else:
            print("OK: ALLOWED_HOSTS ya incluye la IP necesaria")
    
    # 2. Verificar servicio de almacenamiento
    storage_file = "services/storage_service.py"
    if os.path.exists(storage_file):
        with open(storage_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "if not resolved_name:" not in content:
            print("ADVERTENCIA: Servicio de almacenamiento necesita correcciones")
            print("Ejecutando script de correccion...")
            
            try:
                result = subprocess.run([
                    sys.executable, 'scripts/diagnostics/fix_document_download_simple.py'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("OK: Servicio de almacenamiento corregido")
                    fixes_applied.append("Storage Service")
                else:
                    print("ERROR: No se pudo corregir el servicio de almacenamiento")
            except Exception as e:
                print(f"ERROR ejecutando script de correccion: {e}")
        else:
            print("OK: Servicio de almacenamiento ya tiene las correcciones")
    
    return fixes_applied

def commit_changes(fixes_applied):
    """Hacer commit de los cambios."""
    print_section("COMMIT DE CAMBIOS")
    
    if not fixes_applied:
        print("No hay cambios para hacer commit")
        return True
    
    try:
        # Agregar todos los cambios
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR al agregar cambios a Git")
            return False
        
        # Hacer commit
        commit_message = f"Fix production issues: {', '.join(fixes_applied)} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"OK: Commit realizado: {commit_message}")
            return True
        else:
            print("ERROR al hacer commit")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"ERROR en commit: {e}")
        return False

def deploy_to_azure():
    """Desplegar a Azure."""
    print_section("DESPLIEGUE A AZURE")
    
    print("Para desplegar a Azure, ejecuta uno de estos comandos:")
    print()
    print("1. Si usas Azure CLI:")
    print("   az webapp up --name vea-connect-webapp-prod --resource-group tu-resource-group")
    print()
    print("2. Si usas Git deployment:")
    print("   git push azure main")
    print()
    print("3. Si usas Azure DevOps:")
    print("   - Ve a Azure DevOps > Pipelines")
    print("   - Ejecuta el pipeline de despliegue")
    print()
    print("4. Si usas GitHub Actions:")
    print("   - Haz push a la rama main")
    print("   - El workflow se ejecutara automaticamente")
    
    return True

def main():
    """Función principal."""
    print_section("DESPLIEGUE DE CORRECCIONES A AZURE")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar Git
    if not check_git_status():
        print("ERROR: No se puede continuar sin Git")
        return
    
    # Aplicar correcciones
    fixes_applied = apply_fixes()
    
    if fixes_applied:
        print(f"\nCorrecciones aplicadas: {', '.join(fixes_applied)}")
        
        # Hacer commit
        if commit_changes(fixes_applied):
            print("\nOK: Cambios guardados en Git")
            
            # Instrucciones de despliegue
            deploy_to_azure()
        else:
            print("\nERROR: No se pudieron guardar los cambios")
    else:
        print("\nNo se aplicaron correcciones nuevas")
        print("Los archivos ya tienen las correcciones necesarias")
        
        # Instrucciones de despliegue
        deploy_to_azure()
    
    print_section("RESUMEN")
    print("Para completar el despliegue:")
    print("1. Ejecuta el comando de despliegue apropiado")
    print("2. Espera a que se complete el despliegue")
    print("3. Verifica los logs en Azure Portal")
    print("4. Prueba la funcionalidad de descarga de documentos")

if __name__ == "__main__":
    main()
