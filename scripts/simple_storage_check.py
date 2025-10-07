"""
VEA Connect - Verificación Simple del Storage
"""

import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

def check_storage():
    """Verificar contenido del container"""
    print("📦 Verificando container vea-files...")
    
    connection_string = os.getenv('STORAGE_CONNECTION_STRING')
    container_name = os.getenv('STORAGE_CONTAINER_NAME')
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        print(f"✅ Conectado al container: {container_name}")
        
        # Listar blobs
        blobs = container_client.list_blobs()
        blob_list = list(blobs)
        
        if not blob_list:
            print("⚠️ El container está vacío")
            return
        
        print(f"📄 Encontrados {len(blob_list)} archivo(s):")
        print("-" * 50)
        
        for i, blob in enumerate(blob_list, 1):
            print(f"{i:2d}. {blob.name}")
            print(f"    Tamaño: {blob.size:,} bytes")
            print(f"    Modificado: {blob.last_modified}")
            print()
        
        # Verificar tipos de archivo
        file_types = {}
        for blob in blob_list:
            ext = blob.name.split('.')[-1].lower() if '.' in blob.name else 'sin_extension'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print("📊 Resumen por tipo de archivo:")
        for ext, count in file_types.items():
            print(f"   .{ext}: {count} archivo(s)")
        
        # Verificar archivos soportados
        supported_extensions = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'xlsx', 'xls']
        supported_files = [blob for blob in blob_list if blob.name.split('.')[-1].lower() in supported_extensions]
        
        print(f"\n✅ Archivos soportados por el indexer: {len(supported_files)}")
        if supported_files:
            print("   Archivos que pueden ser indexados:")
            for blob in supported_files:
                print(f"   - {blob.name}")
        else:
            print("   ⚠️ No hay archivos en formatos soportados")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_storage()

