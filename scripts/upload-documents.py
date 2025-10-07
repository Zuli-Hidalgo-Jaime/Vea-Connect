"""
VEA Connect - Subir Documentos a Azure Storage
Script para subir documentos al contenedor de Azure Storage (como UploadDocs.ps1)
"""

import os
import sys
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

def load_config():
    """Cargar configuración desde variables de entorno"""
    load_dotenv()
    
    config = {
        "connection_string": os.getenv("STORAGE_CONNECTION_STRING"),
        "container_name": os.getenv("STORAGE_CONTAINER_NAME", "admin-documentos")
    }
    
    if not config["connection_string"]:
        print("❌ Error: STORAGE_CONNECTION_STRING no configurada")
        print("Configura la variable en tu archivo .env")
        sys.exit(1)
    
    return config

def create_container(blob_service_client, container_name):
    """Crear contenedor si no existe"""
    try:
        print(f"📦 Creando contenedor '{container_name}'...")
        blob_service_client.create_container(container_name)
        print(f"✅ Contenedor '{container_name}' creado exitosamente")
        return True
    except Exception as e:
        if "ContainerAlreadyExists" in str(e):
            print(f"ℹ️  Contenedor '{container_name}' ya existe")
            return True
        else:
            print(f"❌ Error al crear contenedor: {str(e)}")
            return False

def upload_file(blob_client, file_path, blob_name):
    """Subir un archivo individual"""
    try:
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print(f"✅ Subido: {blob_name}")
        return True
    except Exception as e:
        print(f"❌ Error al subir {blob_name}: {str(e)}")
        return False

def upload_documents_from_folder(folder_path, container_client, container_name):
    """Subir todos los documentos de una carpeta"""
    if not os.path.exists(folder_path):
        print(f"❌ Carpeta no encontrada: {folder_path}")
        return False
    
    print(f"📁 Subiendo documentos desde: {folder_path}")
    
    success_count = 0
    total_count = 0
    
    # Recursivamente obtener todos los archivos
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Calcular ruta relativa para el blob
            relative_path = os.path.relpath(file_path, folder_path)
            blob_name = relative_path.replace("\\", "/")
            
            total_count += 1
            
            # Crear blob client y subir archivo
            blob_client = container_client.get_blob_client(blob_name)
            
            if upload_file(blob_client, file_path, blob_name):
                success_count += 1
    
    print(f"\n📊 Resultado: {success_count}/{total_count} archivos subidos exitosamente")
    return success_count == total_count

def main():
    """Función principal"""
    print("🚀 VEA Connect - Subir Documentos a Azure Storage")
    print("=" * 50)
    
    # Cargar configuración
    config = load_config()
    
    print(f"📦 Contenedor: {config['container_name']}")
    print(f"🔗 Connection String: {'*' * 20}...")
    print()
    
    try:
        # Crear cliente de Blob Storage
        print("🔌 Conectando a Azure Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(config["connection_string"])
        
        # Crear contenedor
        if not create_container(blob_service_client, config["container_name"]):
            sys.exit(1)
        
        # Obtener cliente del contenedor
        container_client = blob_service_client.get_container_client(config["container_name"])
        
        # Subir documentos de ejemplo
        data_folder = "../data"
        if os.path.exists(data_folder):
            print(f"\n📁 Encontrada carpeta de datos: {data_folder}")
            upload_documents_from_folder(data_folder, container_client, config["container_name"])
        else:
            print(f"\n⚠️  Carpeta de datos no encontrada: {data_folder}")
            print("💡 Crea la carpeta 'data' y coloca algunos documentos PDF para probar")
        
        print("\n" + "=" * 50)
        print("🎉 ¡Proceso completado!")
        print("\n📋 Próximos pasos:")
        print("1. Ejecuta setup-azure-search.py para configurar Azure AI Search")
        print("2. El indexer procesará automáticamente los documentos")
        print("3. Prueba la búsqueda en el portal de Azure")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()




