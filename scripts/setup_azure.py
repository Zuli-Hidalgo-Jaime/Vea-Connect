"""
VEA Connect - Configuración de Azure
Script para configurar recursos de Azure usando Python
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureSetup:
    """Clase para configurar recursos de Azure"""
    
    def __init__(self, subscription_id: str, location: str = "East US"):
        self.subscription_id = subscription_id
        self.location = location
        self.credential = DefaultAzureCredential()
        
        # Clientes de Azure
        self.resource_client = ResourceManagementClient(
            self.credential, subscription_id
        )
        self.search_client = SearchManagementClient(
            self.credential, subscription_id
        )
        self.storage_client = StorageManagementClient(
            self.credential, subscription_id
        )
        self.cognitive_client = CognitiveServicesManagementClient(
            self.credential, subscription_id
        )
    
    def create_resource_group(self, resource_group_name: str) -> bool:
        """Crear grupo de recursos"""
        try:
            logger.info(f"Creando grupo de recursos: {resource_group_name}")
            
            resource_group_params = {
                "location": self.location
            }
            
            result = self.resource_client.resource_groups.create_or_update(
                resource_group_name, resource_group_params
            )
            
            logger.info(f"Grupo de recursos creado: {result.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error al crear grupo de recursos: {str(e)}")
            return False
    
    def save_config(self, config: Dict[str, Any], filename: str = "azure_config.json"):
        """Guardar configuración en archivo"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuración guardada en: {filename}")
        except Exception as e:
            logger.error(f"Error al guardar configuración: {str(e)}")

def main():
    """Función principal para configurar Azure"""
    print("VEA Connect - Configuración de Azure")
    print("===================================")
    
    # Configuración
    subscription_id = input("Ingresa tu Subscription ID de Azure: ").strip()
    resource_group_name = input("Ingresa el nombre del grupo de recursos: ").strip()
    location = input("Ingresa la ubicación (default: East US): ").strip() or "East US"
    
    # Nombres de recursos
    search_service_name = f"vea-connect-search-{int(time.time())}"
    storage_account_name = f"veaconnectstorage{int(time.time())}"
    cognitive_services_name = f"vea-connect-cognitive-{int(time.time())}"
    openai_name = f"vea-connect-openai-{int(time.time())}"
    container_name = "admin-documentos"
    
    # Crear instancia de configuración
    azure_setup = AzureSetup(subscription_id, location)
    
    # Crear recursos
    logger.info("Iniciando configuración de recursos de Azure")
    
    # 1. Crear grupo de recursos
    if not azure_setup.create_resource_group(resource_group_name):
        logger.error("Error al crear grupo de recursos")
        return
    
    # Guardar configuración básica
    config = {
        "azure": {
            "subscription_id": subscription_id,
            "resource_group": resource_group_name,
            "location": location,
            "search_service_name": search_service_name,
            "storage_account_name": storage_account_name,
            "cognitive_services_name": cognitive_services_name,
            "openai_name": openai_name
        },
        "container_name": container_name
    }
    
    azure_setup.save_config(config)
    
    logger.info("Configuración básica de Azure completada")
    logger.info("Nota: Los recursos de Azure se crearán manualmente desde el portal")
    logger.info(f"Archivo de configuración: azure_config.json")

if __name__ == "__main__":
    main()



