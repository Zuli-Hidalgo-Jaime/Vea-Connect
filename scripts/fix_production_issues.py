#!/usr/bin/env python3
"""
Script principal para corregir todos los problemas de producción identificados en los logs.

Problemas a corregir:
1. Error de ALLOWED_HOSTS: '169.254.130.4:8000'
2. Error de descarga de documentos: 'argument of type NoneType is not iterable'
3. Configuración de almacenamiento

Uso: python scripts/fix_production_issues.py
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

def run_script(script_path, description):
    """Ejecutar un script de corrección."""
    print(f"\n🔧 {description}")
    print(f"📁 Ejecutando: {script_path}")
    
    try:
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Advertencias: {result.stderr}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error ejecutando {script_path}: {e}")
        return False

def main():
    """Función principal."""
    print_section("CORRECCIÓN COMPLETA DE PROBLEMAS DE PRODUCCIÓN")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Lista de scripts a ejecutar
    scripts = [
        ("scripts/diagnostics/fix_production_issues.py", "Diagnóstico general de problemas"),
        ("scripts/diagnostics/fix_document_download.py", "Corrección de error de descarga de documentos"),
    ]
    
    results = []
    
    # Ejecutar cada script
    for script_path, description in scripts:
        success = run_script(script_path, description)
        results.append((description, success))
    
    # Resumen final
    print_section("RESUMEN DE CORRECCIONES")
    
    all_success = True
    for description, success in results:
        status = "✅ EXITOSO" if success else "❌ FALLÓ"
        print(f"{status}: {description}")
        if not success:
            all_success = False
    
    if all_success:
        print("\n🎉 TODAS LAS CORRECCIONES APLICADAS EXITOSAMENTE!")
        print("\n📋 Próximos pasos:")
        print("   1. Reinicia la aplicación en Azure App Service")
        print("   2. Verifica que los errores se hayan resuelto")
        print("   3. Monitorea los logs para confirmar que no hay más errores")
    else:
        print("\n⚠️  ALGUNAS CORRECCIONES FALLARON")
        print("\n💡 Recomendaciones:")
        print("   1. Revisa los errores específicos arriba")
        print("   2. Aplica las correcciones manualmente si es necesario")
        print("   3. Contacta al equipo de desarrollo si persisten los problemas")
    
    print(f"\n📝 Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
