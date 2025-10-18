import logging
import azure.functions as func
import os
import sys

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Función para probar el SDK de Azure Communication Messages en Azure Functions"""
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        # Verificar Python path
        python_path = str(sys.path)
        python_version = sys.version
        
        # Verificar módulos instalados
        try:
            import pkg_resources
            installed_packages = [d.project_name for d in pkg_resources.working_set]
            azure_packages = [pkg for pkg in installed_packages if 'azure' in pkg.lower()]
        except Exception as e:
            azure_packages = f"Error: {e}"
        
        # Probar importación del SDK
        sdk_status = "NO DISPONIBLE"
        sdk_version = "N/A"
        client_status = "NO PROBADO"
        message_status = "NO PROBADO"
        
        try:
            import azure.communication.messages
            sdk_status = "DISPONIBLE"
            sdk_version = getattr(azure.communication.messages, '__version__', 'Desconocida')
            
            # Probar importación de clases específicas
            from azure.communication.messages import NotificationMessagesClient
            from azure.communication.messages.models import TextNotificationContent
            
            # Probar creación de cliente
            conn_string = os.getenv('ACS_CONNECTION_STRING')
            if conn_string:
                client = NotificationMessagesClient.from_connection_string(conn_string)
                client_status = "CREADO EXITOSAMENTE"
                
                # Probar envío de mensaje
                channel_id = os.getenv('WHATSAPP_CHANNEL_ID_GUID')
                if channel_id:
                    text_content = TextNotificationContent(
                        channel_registration_id=channel_id,
                        to=["+5215519387611"],
                        content="Prueba desde Azure Functions - SDK funcionando!"
                    )
                    
                    message_responses = client.send(text_content)
                    response = message_responses.receipts[0]
                    
                    if response is not None:
                        message_status = f"ENVIADO EXITOSAMENTE - ID: {response.message_id}"
                    else:
                        message_status = "FALLÓ AL ENVIAR"
                else:
                    message_status = "CHANNEL_ID NO DISPONIBLE"
            else:
                client_status = "CONNECTION_STRING NO DISPONIBLE"
                
        except ImportError as e:
            sdk_status = f"ERROR DE IMPORTACIÓN: {e}"
        except Exception as e:
            sdk_status = f"ERROR: {e}"
        
        # Construir respuesta
        result = {
            "python_version": python_version,
            "python_path": python_path,
            "azure_packages": azure_packages,
            "sdk_status": sdk_status,
            "sdk_version": sdk_version,
            "client_status": client_status,
            "message_status": message_status,
            "environment_vars": {
                "ACS_CONNECTION_STRING": "SET" if os.getenv('ACS_CONNECTION_STRING') else "NOT SET",
                "WHATSAPP_CHANNEL_ID_GUID": os.getenv('WHATSAPP_CHANNEL_ID_GUID', 'NOT SET'),
                "ACS_PHONE_NUMBER": os.getenv('ACS_PHONE_NUMBER', 'NOT SET')
            }
        }
        
        return func.HttpResponse(
            f"SDK Test Results: {result}",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            f"Error en prueba: {str(e)}",
            status_code=500
        )
