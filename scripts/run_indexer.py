"""
VEA Connect - Ejecutar Indexer
Script simple para ejecutar el indexer de Azure AI Search
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def run_indexer():
    """Ejecutar el indexer"""
    search_url = os.getenv('SEARCH_SERVICE_ENDPOINT')
    admin_key = os.getenv('SEARCH_SERVICE_KEY')
    api_version = '2023-11-01'
    
    if not search_url or not admin_key:
        print("Error: Faltan variables de entorno")
        return False
    
    url = f"{search_url}/indexers/vea-connect-indexer/run?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    print("Ejecutando indexer...")
    response = requests.post(url, headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 202:
        print("✅ Indexer ejecutado correctamente")
        print("El indexer está procesando documentos en segundo plano")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    run_indexer()

