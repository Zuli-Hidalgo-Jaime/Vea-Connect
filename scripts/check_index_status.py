"""
VEA Connect - Verificar Estado del Índice e Indexador
Script para revisar el estado del índice y indexador de Azure AI Search
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def check_index_status():
    """Verificar estado del índice"""
    print("🔍 Verificando estado del índice...")
    
    search_url = os.getenv('SEARCH_SERVICE_ENDPOINT')
    admin_key = os.getenv('SEARCH_SERVICE_KEY')
    index_name = os.getenv('SEARCH_INDEX_NAME')
    api_version = '2023-11-01'
    
    if not all([search_url, admin_key, index_name]):
        print("❌ Faltan variables de entorno")
        return
    
    # Verificar índice
    url = f"{search_url}/indexes/{index_name}?api-version={api_version}"
    headers = {"api-key": admin_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            index_data = response.json()
            print("✅ Índice encontrado:")
            print(f"   Nombre: {index_data.get('name')}")
            print(f"   Campos: {len(index_data.get('fields', []))}")
            
            # Mostrar campos
            print("\n📋 Campos del índice:")
            for field in index_data.get('fields', []):
                print(f"   - {field.get('name')} ({field.get('type')})")
            
            # Verificar estadísticas
            stats_url = f"{search_url}/indexes/{index_name}/stats?api-version={api_version}"
            stats_response = requests.get(stats_url, headers=headers)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"\n📊 Estadísticas:")
                print(f"   Documentos: {stats.get('documentCount', 0)}")
                print(f"   Tamaño: {stats.get('storageSize', 0)} bytes")
            else:
                print("⚠️ No se pudieron obtener estadísticas")
                
        else:
            print(f"❌ Error al obtener índice: {response.status_code}")
            print(f"   {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def check_indexer_status():
    """Verificar estado del indexer"""
    print("\n🔄 Verificando estado del indexer...")
    
    search_url = os.getenv('SEARCH_SERVICE_ENDPOINT')
    admin_key = os.getenv('SEARCH_SERVICE_KEY')
    api_version = '2023-11-01'
    
    # Verificar indexer
    url = f"{search_url}/indexers/vea-connect-indexer?api-version={api_version}"
    headers = {"api-key": admin_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            indexer_data = response.json()
            print("✅ Indexer encontrado:")
            print(f"   Nombre: {indexer_data.get('name')}")
            print(f"   Estado: {indexer_data.get('status')}")
            print(f"   Última ejecución: {indexer_data.get('lastResult', {}).get('startTime', 'Nunca')}")
            
            # Verificar historial de ejecución
            history_url = f"{search_url}/indexers/vea-connect-indexer/status?api-version={api_version}"
            history_response = requests.get(history_url, headers=headers)
            if history_response.status_code == 200:
                history = history_response.json()
                executions = history.get('executionHistory', [])
                print(f"\n📈 Historial de ejecuciones: {len(executions)}")
                
                if executions:
                    last_execution = executions[0]
                    print(f"   Última ejecución:")
                    print(f"     - Inicio: {last_execution.get('startTime')}")
                    print(f"     - Estado: {last_execution.get('status')}")
                    print(f"     - Documentos procesados: {last_execution.get('itemsProcessed', 0)}")
                    print(f"     - Errores: {last_execution.get('itemsFailed', 0)}")
                    
                    if last_execution.get('errors'):
                        print(f"   Errores:")
                        for error in last_execution.get('errors', []):
                            print(f"     - {error.get('errorMessage', 'Error desconocido')}")
            else:
                print("⚠️ No se pudo obtener historial")
                
        else:
            print(f"❌ Error al obtener indexer: {response.status_code}")
            print(f"   {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def check_datasource_status():
    """Verificar estado del datasource"""
    print("\n📦 Verificando estado del datasource...")
    
    search_url = os.getenv('SEARCH_SERVICE_ENDPOINT')
    admin_key = os.getenv('SEARCH_SERVICE_KEY')
    api_version = '2023-11-01'
    
    # Verificar datasource
    url = f"{search_url}/datasources/vea-connect-datasource?api-version={api_version}"
    headers = {"api-key": admin_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            datasource_data = response.json()
            print("✅ Datasource encontrado:")
            print(f"   Nombre: {datasource_data.get('name')}")
            print(f"   Tipo: {datasource_data.get('type')}")
            print(f"   Container: {datasource_data.get('container', {}).get('name')}")
        else:
            print(f"❌ Error al obtener datasource: {response.status_code}")
            print(f"   {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Función principal"""
    print("🚀 VEA Connect - Estado del Índice e Indexador")
    print("=" * 60)
    
    check_index_status()
    check_indexer_status()
    check_datasource_status()
    
    print("\n" + "=" * 60)
    print("✅ Verificación completada")

if __name__ == "__main__":
    main()

