import os
from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient, BlobClient, generate_blob_sas,
    generate_container_sas, ContentSettings
)
from django.conf import settings

# Inicializar conexión
def get_blob_service_client():
    account_name = os.getenv("BLOB_ACCOUNT_NAME", settings.BLOB_ACCOUNT_NAME)
    account_key = os.getenv("BLOB_ACCOUNT_KEY", settings.BLOB_ACCOUNT_KEY)
    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={account_name};"
        f"AccountKey={account_key};"
        f"EndpointSuffix=core.windows.net"
    )
    return BlobServiceClient.from_connection_string(conn_str), account_name, account_key

# Subida de archivo al contenedor
def upload_file(bytes_data, file_name, content_type='application/pdf'):
    blob_service_client, account_name, account_key = get_blob_service_client()
    container_name = settings.BLOB_CONTAINER_NAME

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(
        bytes_data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type)
    )

    sas_url = blob_client.url + '?' + generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=file_name,
        account_key=account_key,
        permission="r",
        expiry=datetime.utcnow() + timedelta(hours=3)
    )

    return sas_url

# Listado de archivos subidos
def list_files():
    blob_service_client, account_name, account_key = get_blob_service_client()
    container_name = settings.BLOB_CONTAINER_NAME
    container_client = blob_service_client.get_container_client(container_name)

    blobs = container_client.list_blobs(include=['metadata'])

    sas_token = generate_container_sas(
        account_name=account_name,
        container_name=container_name,
        account_key=account_key,
        permission="r",
        expiry=datetime.utcnow() + timedelta(hours=3)
    )

    files = []
    for blob in blobs:
        files.append({
            "filename": blob.name,
            "url": f"https://{account_name}.blob.core.windows.net/{container_name}/{blob.name}?{sas_token}",
            "metadata": blob.metadata or {}
        })
    return files

# Actualización de metadatos
def update_blob_metadata(file_name, metadata: dict):
    blob_service_client, _, _ = get_blob_service_client()
    container_name = settings.BLOB_CONTAINER_NAME
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

    current_metadata = blob_client.get_blob_properties().metadata or {}
    current_metadata.update(metadata)

    blob_client.set_blob_metadata(metadata=current_metadata)
