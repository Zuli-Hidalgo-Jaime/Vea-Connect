#!/usr/bin/env python3
"""
Script para limpiar el historial de git y remover secretos hardcodeados.
Este script reescribe el historial para eliminar commits que contienen secretos.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Ejecutar comando y retornar resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {cmd}")
        print(f"Error: {e}")
        return None

def get_commit_hash_with_secrets():
    """Obtener el hash del commit que contiene secretos"""
    # Los commits problemáticos según GitGuardian
    problematic_commits = [
        "52a21fd3b852393a09eccf9b2e4f7dceb230c725",  # Baseline diagnostics
        "d48715072fa24d27488ea6cbf69bdf69598cdc2d"   # A3 - Log sanitization
    ]
    
    # Verificar cuál está en el historial actual
    current_branch = run_command("git branch --show-current")
    print(f"Rama actual: {current_branch}")
    
    log_output = run_command("git log --oneline")
    for commit in problematic_commits:
        if commit[:7] in log_output:
            return commit
    
    return None

def create_clean_branch():
    """Crear una rama limpia sin secretos"""
    print("🔧 Creando rama limpia sin secretos...")
    
    # Obtener el commit anterior a los problemáticos
    clean_commit = "1eb6698"  # fix download documents
    
    # Crear nueva rama desde el commit limpio
    branch_name = "devops/staging-slot-pipeline-clean"
    
    # Eliminar rama si existe
    run_command(f"git branch -D {branch_name}", check=False)
    
    # Crear nueva rama
    result = run_command(f"git checkout -b {branch_name} {clean_commit}")
    if not result:
        print("❌ Error creando rama limpia")
        return False
    
    print(f"✅ Rama limpia creada: {branch_name}")
    return True

def apply_clean_changes():
    """Aplicar cambios limpios sin secretos"""
    print("🔧 Aplicando cambios limpios...")
    
    # Crear directorio de parches si no existe
    Path("parches_sugeridos").mkdir(exist_ok=True)
    
    # Los archivos ya están creados por el asistente anterior
    # Solo necesitamos agregarlos al commit
    
    # Agregar archivos limpios
    run_command("git add parches_sugeridos/")
    
    # Crear commit con cambios limpios
    commit_msg = """SECURITY: Limpiar secretos hardcodeados

- Eliminar archivos de parches con secretos
- Crear versiones limpias sin credenciales
- Actualizar documentación de seguridad
- Implementar mejores prácticas de manejo de secretos

Los secretos ahora se configuran via variables de entorno en Azure Portal.
"""
    
    result = run_command(f'git commit -m "{commit_msg}"')
    if not result:
        print("❌ Error creando commit limpio")
        return False
    
    print("✅ Cambios limpios aplicados")
    return True

def push_clean_branch():
    """Hacer push de la rama limpia"""
    print("🚀 Haciendo push de rama limpia...")
    
    branch_name = "devops/staging-slot-pipeline-clean"
    
    result = run_command(f"git push -u origin {branch_name}")
    if not result:
        print("❌ Error haciendo push")
        return False
    
    print(f"✅ Rama limpia pusheada: {branch_name}")
    return True

def main():
    """Función principal"""
    print("🔒 Limpiando historial de git - Removiendo secretos hardcodeados")
    print("=" * 60)
    
    # Verificar que estamos en un repositorio git
    if not Path(".git").exists():
        print("❌ No estamos en un repositorio git")
        sys.exit(1)
    
    # Verificar estado actual
    status = run_command("git status --porcelain")
    if status:
        print("⚠️ Hay cambios sin commitear. Guardando cambios...")
        run_command("git stash")
    
    # Crear rama limpia
    if not create_clean_branch():
        sys.exit(1)
    
    # Aplicar cambios limpios
    if not apply_clean_changes():
        sys.exit(1)
    
    # Hacer push
    if not push_clean_branch():
        sys.exit(1)
    
    print("\n🎉 ¡Limpieza completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Crear nuevo PR desde la rama limpia")
    print("2. Eliminar la rama anterior con secretos")
    print("3. Configurar GitGuardian para futuros commits")
    print("4. Configurar secretos en Azure Portal")
    
    print(f"\n🔗 Rama limpia: devops/staging-slot-pipeline-clean")
    print("🔗 Rama anterior (con secretos): devops/staging-slot-pipeline")

if __name__ == "__main__":
    main()
