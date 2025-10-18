# apps/documents/utils.py
import requests
import os

def procesar_documento_en_function(blob_url: str, nombre_archivo: str):
    endpoint = os.getenv("AZURE_FUNCTION_PROCESS_DOCUMENT_URL")
    payload = {
        "file_url": blob_url,
        "filename": nombre_archivo
    }
    try:
        response = requests.post(endpoint, json=payload)
        return response.status_code == 200
    except Exception as e:
        print("Error llamando a la función:", e)
        return False
