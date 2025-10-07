"""
VEA Connect - Verificar Container de Storage
Script para revisar qué documentos hay en el container vea-files
"""

import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

def check_storage_container():
    """Verificar contenido del container vea-files"""
    print("📦 Verificando container vea-files...")
    
    connection_string = os.getenv('STORAGE_CONNECTION_STRING')
    container_name = os.getenv('STORAGE_CONTAINER_NAME')
    
    if not connection_string or not container_name:
        print("❌ Faltan variables de entorno para Storage")
        return
    
    try:
        # Crear cliente de Blob Storage
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        print(f"✅ Conectado al container: {container_name}")
        
        # Listar blobs
        blobs = container_client.list_blobs()
        blob_list = list(blobs)
        
        if not blob_list:
            print("⚠️ El container está vacío")
            print("💡 Necesitas subir documentos para que el indexer los procese")
            return
        
        print(f"📄 Encontrados {len(blob_list)} archivo(s):")
        print("-" * 60)
        
        for i, blob in enumerate(blob_list, 1):
            print(f"{i:2d}. {blob.name}")
            print(f"    Tamaño: {blob.size:,} bytes")
            print(f"    Modificado: {blob.last_modified}")
            print(f"    URL: {blob.url}")
            print()
        
        # Verificar tipos de archivo
        file_types = {}
        for blob in blob_list:
            ext = blob.name.split('.')[-1].lower() if '.' in blob.name else 'sin_extension'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print("📊 Resumen por tipo de archivo:")
        for ext, count in file_types.items():
            print(f"   .{ext}: {count} archivo(s)")
        
        # Verificar si hay documentos que el indexer pueda procesar
        supported_extensions = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'xlsx', 'xls']
        supported_files = [blob for blob in blob_list if blob.name.split('.')[-1].lower() in supported_extensions]
        
        print(f"\n✅ Archivos soportados por el indexer: {len(supported_files)}")
        if supported_files:
            print("   Archivos que pueden ser indexados:")
            for blob in supported_files:
                print(f"   - {blob.name}")
        else:
            print("   ⚠️ No hay archivos en formatos soportados")
            print("   💡 Formatos soportados: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, XLSX, XLS")
        
    except Exception as e:
        print(f"❌ Error al acceder al container: {str(e)}")

def main():
    """Función principal"""
    print("🚀 VEA Connect - Verificación del Container de Storage")
    print("=" * 60)
    
    check_storage_container()
    
    print("\n" + "=" * 60)
    print("✅ Verificación completada")

if __name__ == "__main__":
    main()
