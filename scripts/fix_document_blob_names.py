import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')  # Cambiado a producción
django.setup()

from apps.documents.models import Document
from django.conf import settings
from azure.storage.blob import BlobServiceClient

print("USANDO BASE DE DATOS:", settings.DATABASES)

# Conexión a Azure Blob Storage
account_url = f"https://{settings.BLOB_ACCOUNT_NAME}.blob.core.windows.net"
credential = settings.BLOB_ACCOUNT_KEY
container_name = settings.BLOB_CONTAINER_NAME
blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
container_client = blob_service_client.get_container_client(container_name)

def blob_exists(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    return blob_client.exists()

def main():
    print("Corrigiendo documentos en la base de datos...")
    cambios = 0
    for doc in Document.objects.all():
        original_name = doc.file.name
        print(f"Doc {doc.pk}: file.name='{original_name}'")
        if not original_name:
            print(f"  → Sin archivo asociado.")
            continue
        if blob_exists(original_name):
            print(f"  ✔ '{original_name}' existe en Azure.")
            continue
        # Probar sin el prefijo 'documents/'
        if original_name.startswith('documents/'):
            alt_name = original_name[len('documents/'):]
            if blob_exists(alt_name):
                print(f"  🛠 Corrigiendo: '{original_name}' → '{alt_name}' en BD...")
                doc.file.name = alt_name
                doc.save(update_fields=["file"])
                cambios += 1
            else:
                print(f"  ✗ '{original_name}' y '{alt_name}' NO existen en Azure.")
        else:
            print(f"  ✗ '{original_name}' NO existe en Azure y no tiene prefijo 'documents/'.")
    print(f"\nTotal de documentos corregidos: {cambios}")

if __name__ == "__main__":
    main() 