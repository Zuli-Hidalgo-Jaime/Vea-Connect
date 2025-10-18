#!/usr/bin/env python
"""
Script para limpiar referencias a Redis del proyecto.
Este script identifica y ayuda a eliminar referencias obsoletas a Redis.
"""

import os
import re
from pathlib import Path

def find_redis_references():
    """Encontrar todas las referencias a Redis en el proyecto"""
    project_root = Path(__file__).parent.parent.parent
    redis_references = []
    
    # Patrones para buscar referencias a Redis
    patterns = [
        r'import\s+redis',
        r'from\s+redis',
        r'redis\.Redis\(',
        r'REDIS_URL',
        r'REDIS_TTL',
        r'django_redis',
        r'RedisCache',
        r'redis_cache',
        r'redis_client',
        r'redis\.from_url',
        r'redis\.StrictRedis',
    ]
    
    # Excluir directorios
    exclude_dirs = {
        '.git', '__pycache__', 'venv', 'env', 'node_modules', 
        'staticfiles', 'media', '.pytest_cache', 'migrations'
    }
    
    # Excluir archivos
    exclude_files = {
        'cleanup_redis_references.py', 'test_redis_cleanup.py'
    }
    
    for root, dirs, files in os.walk(project_root):
        # Excluir directorios
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(('.py', '.yml', '.yaml', '.env', '.txt', '.md')):
                if file in exclude_files:
                    continue
                    
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    redis_references.append({
                                        'file': str(file_path.relative_to(project_root)),
                                        'line': line_num,
                                        'content': line.strip(),
                                        'pattern': pattern
                                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return redis_references

def generate_cleanup_report():
    """Generar un reporte de limpieza de Redis"""
    print("🔍 Buscando referencias a Redis en el proyecto...")
    
    references = find_redis_references()
    
    if not references:
        print("✅ No se encontraron referencias a Redis")
        return
    
    print(f"\n📊 Se encontraron {len(references)} referencias a Redis:")
    print("=" * 80)
    
    # Agrupar por archivo
    files = {}
    for ref in references:
        if ref['file'] not in files:
            files[ref['file']] = []
        files[ref['file']].append(ref)
    
    for file_path, refs in files.items():
        print(f"\n📁 {file_path}:")
        for ref in refs:
            print(f"  Línea {ref['line']}: {ref['content']}")
            print(f"    Patrón: {ref['pattern']}")
    
    print("\n" + "=" * 80)
    print("📋 Acciones recomendadas:")
    print("1. Revisar cada referencia y determinar si es necesaria")
    print("2. Reemplazar imports de redis con django.core.cache")
    print("3. Actualizar configuraciones de caché")
    print("4. Eliminar variables de entorno relacionadas con Redis")
    print("5. Actualizar documentación")

def check_environment_variables():
    """Verificar variables de entorno relacionadas con Redis"""
    print("\n🔧 Verificando variables de entorno...")
    
    redis_env_vars = [
        'AZURE_REDIS_URL',
        'AZURE_REDIS_CONNECTIONSTRING',
        'REDIS_URL',
        'REDIS_TTL_SECS',
        'REDIS_HOST',
        'REDIS_PORT',
        'REDIS_PASSWORD'
    ]
    
    found_vars = []
    for var in redis_env_vars:
        if os.environ.get(var):
            found_vars.append(var)
    
    if found_vars:
        print(f"⚠️  Variables de entorno de Redis encontradas: {', '.join(found_vars)}")
        print("   Considera eliminarlas si no se usan")
    else:
        print("✅ No se encontraron variables de entorno de Redis")

if __name__ == '__main__':
    print("🧹 Script de limpieza de referencias a Redis")
    print("=" * 50)
    
    generate_cleanup_report()
    check_environment_variables()
    
    print("\n🏁 Análisis completado")
