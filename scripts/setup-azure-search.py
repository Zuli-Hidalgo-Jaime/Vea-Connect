"""
VEA Connect - Configuración de Azure AI Search
Script para configurar Azure AI Search usando los archivos JSON (como modify-search.cmd)
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def load_config():
    """Cargar configuración desde variables de entorno"""
    config = {
        "search_url": os.getenv("SEARCH_SERVICE_ENDPOINT"),
        "admin_key": os.getenv("SEARCH_SERVICE_KEY"),
        "api_version": "2023-11-01"
    }
    
    if not config["search_url"] or not config["admin_key"]:
        print("Error: Variables de entorno faltantes")
        print("Configura SEARCH_SERVICE_ENDPOINT y SEARCH_SERVICE_KEY en tu archivo .env")
        sys.exit(1)
    
    return config

def make_request(method: str, url: str, headers: Dict[str, str], data: str = None) -> bool:
    """Realizar petición HTTP"""
    try:
        if method.upper() == "PUT":
            response = requests.put(url, headers=headers, data=data)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, data=data)
        else:
            print(f"Método HTTP no soportado: {method}")
            return False
        
        if response.status_code in [200, 201, 204]:
            print(f"{method} {url} - Status: {response.status_code}")
            return True
        else:
            print(f"{method} {url} - Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error en petición: {str(e)}")
        return False

def update_skillset(config: Dict[str, Any]) -> bool:
    """Actualizar skillset"""
    print("-----")
    print("Actualizando skillset...")
    
    # Leer archivo JSON
    skillset_path = "../config/azure/vea-connect-skillset.json"
    if not os.path.exists(skillset_path):
        print(f"Archivo no encontrado: {skillset_path}")
        return False
    
    with open(skillset_path, 'r', encoding='utf-8') as f:
        skillset_data = f.read()
    
    # URL y headers
    url = f"{config['search_url']}/skillsets/vea-connect-skillset?api-version={config['api_version']}"
    headers = {
        "Content-Type": "application/json",
        "api-key": config["admin_key"]
    }
    
    return make_request("PUT", url, headers, skillset_data)

def update_index(config: Dict[str, Any]) -> bool:
    """Actualizar índice"""
    print("-----")
    print("Actualizando índice...")
    
    # Leer archivo JSON
    index_path = "../config/azure/vea-connect-index.json"
    if not os.path.exists(index_path):
        print(f"Archivo no encontrado: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = f.read()
    
    # URL y headers
    url = f"{config['search_url']}/indexes/vea-connect-index?api-version={config['api_version']}"
    headers = {
        "Content-Type": "application/json",
        "api-key": config["admin_key"]
    }
    
    return make_request("PUT", url, headers, index_data)

def update_datasource(config: Dict[str, Any]) -> bool:
    """Actualizar datasource"""
    print("-----")
    print("Actualizando datasource...")
    
    # Leer archivo JSON
    datasource_path = "../config/azure/vea-connect-datasource.json"
    if not os.path.exists(datasource_path):
        print(f"Archivo no encontrado: {datasource_path}")
        return False
    
    with open(datasource_path, 'r', encoding='utf-8') as f:
        datasource_data = f.read()
    
    # URL y headers
    url = f"{config['search_url']}/datasources/vea-connect-datasource?api-version={config['api_version']}"
    headers = {
        "Content-Type": "application/json",
        "api-key": config["admin_key"]
    }
    
    return make_request("PUT", url, headers, datasource_data)

def update_indexer(config: Dict[str, Any]) -> bool:
    """Actualizar indexer"""
    print("-----")
    print("Actualizando indexer...")
    
    # Leer archivo JSON
    indexer_path = "../config/azure/vea-connect-indexer.json"
    if not os.path.exists(indexer_path):
        print(f"Archivo no encontrado: {indexer_path}")
        return False
    
    with open(indexer_path, 'r', encoding='utf-8') as f:
        indexer_data = f.read()
    
    # URL y headers
    url = f"{config['search_url']}/indexers/vea-connect-indexer?api-version={config['api_version']}"
    headers = {
        "Content-Type": "application/json",
        "api-key": config["admin_key"]
    }
    
    return make_request("PUT", url, headers, indexer_data)

def reset_indexer(config: Dict[str, Any]) -> bool:
    """Resetear indexer"""
    print("-----")
    print("Reseteando indexer...")
    
    url = f"{config['search_url']}/indexers/vea-connect-indexer/reset?api-version={config['api_version']}"
    headers = {
        "Content-Type": "application/json",
        "Content-Length": "0",
        "api-key": config["admin_key"]
    }
    
    return make_request("POST", url, headers)

def run_indexer(config: Dict[str, Any]) -> bool:
    """Ejecutar indexer"""
    print("-----")
    print("Ejecutando indexer...")
    
    url = f"{config['search_url']}/indexers/vea-connect-indexer/run?api-version={config['api_version']}"
    headers = {
        "Content-Type": "application/json",
        "Content-Length": "0",
        "api-key": config["admin_key"]
    }
    
    return make_request("POST", url, headers)

def main():
    """Función principal"""
    print("VEA Connect - Configuración de Azure AI Search")
    print("=" * 50)
    
    # Cargar configuración
    config = load_config()
    
    print(f"URL de búsqueda: {config['search_url']}")
    print(f"API Key: {'*' * len(config['admin_key'])}")
    print()
    
    # Ejecutar pasos
    steps = [
        ("Actualizar skillset", update_skillset),
        ("Actualizar índice", update_index),
        ("Actualizar datasource", update_datasource),
        ("Actualizar indexer", update_indexer),
        ("Resetear indexer", reset_indexer),
        ("Ejecutar indexer", run_indexer)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        
        if step_func(config):
            success_count += 1
            print(f"{step_name} completado")
        else:
            print(f"{step_name} falló")
            break
        
        # Esperar un poco entre pasos
        if step_name != "Ejecutar indexer":
            print("Esperando...")
            time.sleep(2)
    
    print("\n" + "=" * 50)
    print(f"Resultado: {success_count}/{len(steps)} pasos completados")
    
    if success_count == len(steps):
        print("Configuración completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Sube documentos al contenedor de Azure Storage")
        print("2. El indexer procesará automáticamente los documentos")
        print("3. Prueba la búsqueda en el portal de Azure")
    else:
        print("Algunos pasos fallaron. Revisa la configuración.")
        print("\nVerifica:")
        print("- Que las variables de entorno estén configuradas")
        print("- Que los archivos JSON existan en config/azure/")
        print("- Que el servicio de Azure AI Search esté funcionando")

if __name__ == "__main__":
    main()


