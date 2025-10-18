import os
import json
import io
import zipfile
from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient, generate_blob_sas, generate_container_sas,
    ContentSettings
)
from django.conf import settings
import requests

# Conexión base
def get_blob_service_client():
    """Obtiene el cliente de servicio de Azure Blob Storage."""
    try:
        # Verificar si Azure está deshabilitado
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            raise ValueError("Azure Blob Storage está deshabilitado")
            
        account_name = settings.BLOB_ACCOUNT_NAME
        account_key = settings.BLOB_ACCOUNT_KEY
        if not account_name or not account_key:
            raise ValueError("BLOB_ACCOUNT_NAME y BLOB_ACCOUNT_KEY son requeridos")
        
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        return BlobServiceClient.from_connection_string(connect_str)
    except Exception as e:
        print(f"Error al crear el cliente de Blob Storage: {str(e)}")
        raise

# Subida de archivo
def upload_file(bytes_data, file_name, content_type='application/pdf'):
    """Sube un archivo a Azure Blob Storage."""
    try:
        # Verificar si Azure está deshabilitado
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            print(f"Azure Blob Storage deshabilitado. Omitiendo subida de {file_name}")
            return None
            
        container_name = settings.BLOB_CONTAINER_NAME
        if not container_name:
            raise ValueError("BLOB_CONTAINER_NAME es requerido")

        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        
        blob_client.upload_blob(bytes_data, overwrite=True, content_settings=ContentSettings(content_type=content_type))

        sas_token = generate_blob_sas(
            account_name=settings.BLOB_ACCOUNT_NAME,
            container_name=container_name,
            blob_name=file_name,
            account_key=settings.BLOB_ACCOUNT_KEY,
            permission="r",
            expiry=datetime.utcnow() + timedelta(hours=3)
        )
        
        return f"{blob_client.url}?{sas_token}"
    except Exception as e:
        print(f"Error al subir el archivo {file_name}: {str(e)}")
        raise

# Obtención de todos los archivos
def get_all_files():
    """Obtiene todos los archivos del contenedor."""
    try:
        account_name = settings.BLOB_ACCOUNT_NAME
        account_key = settings.BLOB_ACCOUNT_KEY
        container_name = settings.BLOB_CONTAINER_NAME
        
        if not all([account_name, account_key, container_name]):
            raise ValueError("Configuración incompleta de Azure Blob Storage")
        
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(container_name)
        blob_list = container_client.list_blobs(include='metadata')
        
        sas = generate_container_sas(
            account_name, container_name,
            account_key=account_key,
            permission="r",
            expiry=datetime.utcnow() + timedelta(hours=3)
        )

        files = []
        converted_files = {}

        # Aquí se leen los metadatos de los blobs para verificar si han sido procesados
        for blob in blob_list:
            if not blob.name.startswith('converted/'):
                files.append({
                    "filename": blob.name,
                    "converted": blob.metadata.get('converted', 'false') == 'true' if blob.metadata else False,
                    "embeddings_added": blob.metadata.get('embeddings_added', 'false') == 'true' if blob.metadata else False,
                    "fullpath": f"https://{account_name}.blob.core.windows.net/{container_name}/{blob.name}?{sas}",
                    "converted_path": ""
                })
            else:
                # Aquí se almacenan las referencias a los archivos procesados en la carpeta converted/
                converted_files[blob.name] = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob.name}?{sas}"

        # Aquí se verifica si existe un archivo procesado en la carpeta converted/ para cada archivo original
        for file in files:
            converted_filename = f"converted/{file['filename']}.zip"
            if converted_filename in converted_files:
                file['converted'] = True
                file['converted_path'] = converted_files[converted_filename]
            
            # Se agrega almacenamiento del texto extraído por Azure Computer Vision en la carpeta converted/ para futura indexación en Azure AI Search
            # Check if extracted text exists for this file
            base_name = os.path.splitext(file['filename'])[0]
            json_blob_name = f"converted/{base_name}_extracted_text.json"
            if json_blob_name in converted_files:
                file['has_extracted_text'] = True
                file['extracted_text_path'] = converted_files[json_blob_name]
            else:
                file['has_extracted_text'] = False

        return files
    except Exception as e:
        print(f"Error al obtener archivos: {str(e)}")
        raise

# Agregar o actualizar metadatos
def upsert_blob_metadata(file_name, metadata):
    """Actualiza los metadatos de un blob."""
    try:
        container_name = settings.BLOB_CONTAINER_NAME
        if not container_name:
            raise ValueError("BLOB_CONTAINER_NAME es requerido")
            
        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

        blob_metadata = blob_client.get_blob_properties().metadata
        blob_metadata.update(metadata)
        blob_client.set_blob_metadata(metadata=blob_metadata)
    except Exception as e:
        print(f"Error al actualizar metadatos de {file_name}: {str(e)}")
        raise

def upload_to_blob(file_or_buffer, blob_name):
    """
    Sube un archivo a Azure Blob Storage.
    file_or_buffer puede ser una ruta (str/Path) o un buffer (BytesIO).
    """
    try:
        # Verificar si los signals de Azure están deshabilitados
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            print(f"Azure signals deshabilitados. Omitiendo subida de {blob_name}")
            return None

        print(f"Intentando subir {blob_name} a Azure Blob Storage...")

        if not blob_name:
            raise ValueError("blob_name es requerido")

        if not all([settings.BLOB_ACCOUNT_NAME, settings.BLOB_ACCOUNT_KEY, settings.BLOB_CONTAINER_NAME]):
            raise ValueError("Configuración incompleta de Azure Blob Storage")

        print(f"Cuenta: {settings.BLOB_ACCOUNT_NAME}, Contenedor: {settings.BLOB_CONTAINER_NAME}")

        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(
            container=settings.BLOB_CONTAINER_NAME,
            blob=blob_name
        )

        # Si es ruta, abrir el archivo; si es buffer, usarlo directamente
        if isinstance(file_or_buffer, (str, bytes, os.PathLike)):
            with open(file_or_buffer, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
        else:
            # Asumimos que es un buffer tipo BytesIO
            file_or_buffer.seek(0)
            blob_client.upload_blob(file_or_buffer, overwrite=True)

        print("Subida exitosa.")
        return blob_client.url

    except Exception as e:
        print(f"Error en upload_to_blob: {str(e)}")
        raise

def save_extracted_text_to_blob(original_blob_name, extracted_text, metadata=None):
    """
    Save extracted text from Azure Computer Vision to the converted/ folder in Azure Blob Storage.
    
    This function follows the existing pattern of storing processed documents in the converted/ folder
    for future indexing in Azure AI Search.
    
    Args:
        original_blob_name (str): Name of the original blob file
        extracted_text (str): Text extracted by Azure Computer Vision
        metadata (dict, optional): Additional metadata to include
        
    Returns:
        str: URL of the uploaded blob, or None if upload failed
    """
    try:
        # Se agrega almacenamiento del texto extraído por Azure Computer Vision en la carpeta converted/ para futura indexación en Azure AI Search
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            print(f"Azure signals disabled. Skipping text storage for {original_blob_name}")
            return None

        if not extracted_text:
            print(f"No extracted text provided for {original_blob_name}")
            return None

        # Create JSON with extracted text and metadata
        text_data = {
            "original_file": original_blob_name,
            "extracted_text": extracted_text,
            "extraction_date": datetime.utcnow().isoformat(),
            "source": "azure_computer_vision",
            "text_length": len(extracted_text),
            "metadata": metadata or {}
        }

        # Convert to JSON string
        json_content = json.dumps(text_data, ensure_ascii=False, indent=2)
        
        # Create blob name following existing pattern
        base_name = os.path.splitext(original_blob_name)[0]
        json_blob_name = f"converted/{base_name}_extracted_text.json"
        
        # Upload JSON to blob storage
        buffer = io.BytesIO(json_content.encode('utf-8'))
        url = upload_to_blob(buffer, json_blob_name)
        
        if url:
            print(f"Extracted text saved to blob: {json_blob_name}")
            return url
        else:
            print(f"Failed to save extracted text for {original_blob_name}")
            return None

    except Exception as e:
        print(f"Error saving extracted text for {original_blob_name}: {str(e)}")
        return None


def update_zip_with_extracted_text(original_blob_name, extracted_text, metadata=None):
    """
    Update existing ZIP file in converted/ folder with extracted text from Azure Computer Vision.
    
    This function updates the ZIP file created by the document signals to include the extracted text
    for future indexing in Azure AI Search.
    
    Args:
        original_blob_name (str): Name of the original blob file
        extracted_text (str): Text extracted by Azure Computer Vision
        metadata (dict, optional): Additional metadata to include
        
    Returns:
        str: URL of the updated blob, or None if update failed
    """
    try:
        # Se agrega almacenamiento del texto extraído por Azure Computer Vision en la carpeta converted/ para futura indexación en Azure AI Search
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            print(f"Azure signals disabled. Skipping ZIP update for {original_blob_name}")
            return None

        if not extracted_text:
            print(f"No extracted text provided for {original_blob_name}")
            return None

        # Create blob name following existing pattern
        zip_blob_name = f"converted/{original_blob_name}.zip"
        
        # Get the existing ZIP from blob storage
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(settings.BLOB_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(zip_blob_name)
        
        if not blob_client.exists():
            print(f"ZIP file not found: {zip_blob_name}")
            return None

        # Download existing ZIP
        zip_data = blob_client.download_blob().readall()
        
        # Create new ZIP with extracted text
        buffer = io.BytesIO(zip_data)
        new_buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'r') as old_zip:
            with zipfile.ZipFile(new_buffer, 'w') as new_zip:
                # Copy all existing files
                for item in old_zip.infolist():
                    if item.filename != 'extracted_text.json':  # Skip old extracted_text.json
                        new_zip.writestr(item, old_zip.read(item.filename))
                
                # Add updated extracted text
                extracted_text_data = {
                    "extracted_text": extracted_text,
                    "extraction_status": "completed",
                    "extraction_date": datetime.utcnow().isoformat(),
                    "source": "azure_computer_vision",
                    "text_length": len(extracted_text),
                    "metadata": metadata or {}
                }
                
                new_zip.writestr('extracted_text.json', json.dumps(extracted_text_data, ensure_ascii=False, indent=2))
        
        # Upload updated ZIP
        new_buffer.seek(0)
        url = upload_to_blob(new_buffer, zip_blob_name)
        
        if url:
            print(f"ZIP updated with extracted text: {zip_blob_name}")
            return url
        else:
            print(f"Failed to update ZIP for {original_blob_name}")
            return None

    except Exception as e:
        print(f"Error updating ZIP for {original_blob_name}: {str(e)}")
        return None


def get_extracted_text_from_blob(original_blob_name):
    """
    Retrieve extracted text from blob storage for a given original file.
    
    This function reads the extracted text from either the JSON file or ZIP file
    stored in the converted/ folder for future indexing in Azure AI Search.
    
    Args:
        original_blob_name (str): Name of the original blob file
        
    Returns:
        dict: Extracted text data with metadata, or None if not found
    """
    try:
        # Se agrega almacenamiento del texto extraído por Azure Computer Vision en la carpeta converted/ para futura indexación en Azure AI Search
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            print(f"Azure signals disabled. Skipping text retrieval for {original_blob_name}")
            return None

        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(settings.BLOB_CONTAINER_NAME)
        
        # Try to get from JSON file first
        base_name = os.path.splitext(original_blob_name)[0]
        json_blob_name = f"converted/{base_name}_extracted_text.json"
        json_blob_client = container_client.get_blob_client(json_blob_name)
        
        if json_blob_client.exists():
            json_data = json_blob_client.download_blob().readall()
            return json.loads(json_data.decode('utf-8'))
        
        # Try to get from ZIP file
        zip_blob_name = f"converted/{original_blob_name}.zip"
        zip_blob_client = container_client.get_blob_client(zip_blob_name)
        
        if zip_blob_client.exists():
            zip_data = zip_blob_client.download_blob().readall()
            buffer = io.BytesIO(zip_data)
            
            with zipfile.ZipFile(buffer, 'r') as zip_file:
                if 'extracted_text.json' in zip_file.namelist():
                    extracted_text_data = zip_file.read('extracted_text.json')
                    return json.loads(extracted_text_data.decode('utf-8'))
        
        print(f"No extracted text found for {original_blob_name}")
        return None

    except Exception as e:
        print(f"Error retrieving extracted text for {original_blob_name}: {str(e)}")
        return None


def trigger_document_processing(blob_name):
    """
    Llama a la Azure Function con un HTTP Trigger para iniciar el procesamiento.
    """
    try:
        function_url = settings.FUNCTION_APP_URL
        function_key = settings.FUNCTION_APP_KEY

        if not function_url or not function_key:
            print("Advertencia: FUNCTION_APP_URL o FUNCTION_APP_KEY no están configuradas. Omitiendo trigger.")
            return None

        headers = {
            'Content-Type': 'application/json',
            'x-functions-key': function_key
        }
        
        # El cuerpo del payload puede ajustarse a lo que tu Azure Function espere.
        # Por ejemplo, el nombre del blob que debe procesar.
        payload = {
            'blob_name': blob_name
        }

        print(f"Llamando a Azure Function para procesar: {blob_name}")
        
        response = requests.post(function_url, headers=headers, json=payload, timeout=30)
        
        response.raise_for_status()  # Lanza una excepción para respuestas 4xx/5xx

        print(f"Llamada a Azure Function exitosa. Status: {response.status_code}")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error al llamar a la Azure Function: {str(e)}")
        # Aquí podrías reintentar o registrar el fallo para un procesamiento posterior
        return None
    except Exception as e:
        print(f"Error inesperado al disparar la función: {str(e)}")
        return None
