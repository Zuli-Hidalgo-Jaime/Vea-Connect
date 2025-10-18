#!/usr/bin/env python3
"""
Ejemplo completo de WhatsApp usando el SDK oficial de Azure Communication Advanced Messages
Basado en la documentación oficial de Microsoft: https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/messages/send-messages
"""

import os
import json

def load_local_settings():
    """Carga las variables de entorno desde local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        values = settings.get('Values', {})
        
        # Cargar variables críticas
        critical_vars = [
            'ACS_CONNECTION_STRING',
            'ACS_PHONE_NUMBER',
            'WHATSAPP_CHANNEL_ID_GUID'
        ]
        
        for var in critical_vars:
            value = values.get(var)
            if value:
                os.environ[var] = value
                print(f"Cargada: {var}")
            else:
                print(f"No encontrada: {var}")
        
        return True
        
    except Exception as e:
        print(f"Error cargando variables: {e}")
        return False

class WhatsAppAdvancedMessagesExample:
    """
    Ejemplo completo usando el SDK oficial de Azure Communication Advanced Messages
    """
    
    def __init__(self):
        print("Azure Communication Services - Advanced Messages SDK Example")
        
        # Obtener configuración desde variables de entorno
        self.connection_string = os.getenv("ACS_CONNECTION_STRING")
        self.phone_number = os.getenv("ACS_PHONE_NUMBER")  # Número del bot
        self.channel_registration_id = os.getenv("WHATSAPP_CHANNEL_ID_GUID")
        self.recipient_number = "+5215519387611"  # Número de prueba
        
        print(f"Connection String: {'SET' if self.connection_string else 'NOT SET'}")
        print(f"Phone Number: {self.phone_number}")
        print(f"Channel Registration ID: {self.channel_registration_id}")
        print(f"Recipient Number: {self.recipient_number}")
    
    def send_text_message(self):
        """Envía un mensaje de texto usando el SDK oficial"""
        try:
            from azure.communication.messages import NotificationMessagesClient
            from azure.communication.messages.models import TextNotificationContent
            
            print("\nEnviando mensaje de texto...")
            
            # Crear cliente usando connection string
            messaging_client = NotificationMessagesClient.from_connection_string(self.connection_string)
            
            # Configurar mensaje de texto
            text_options = TextNotificationContent(
                channel_registration_id=self.channel_registration_id,
                to=[self.recipient_number],
                content="Hola! Soy el bot de VEA Connect. Este es un mensaje de texto usando el SDK oficial de Advanced Messages."
            )
            
            # Enviar mensaje
            message_responses = messaging_client.send(text_options)
            response = message_responses.receipts[0]
            
            if response is not None:
                print(f"EXITO - Mensaje de texto enviado correctamente")
                print(f"  Message ID: {response.message_id}")
                print(f"  To: {response.to}")
                return True
            else:
                print("ERROR - El mensaje falló al enviar")
                return False
                
        except ImportError as e:
            print(f"ERROR - No se pudo importar el SDK: {e}")
            print("Instalar con: pip install azure-communication-messages")
            return False
        except Exception as e:
            print(f"ERROR - Error enviando mensaje: {e}")
            return False
    
    def send_image_message(self):
        """Envía un mensaje con imagen usando el SDK oficial"""
        try:
            from azure.communication.messages import NotificationMessagesClient
            from azure.communication.messages.models import ImageNotificationContent
            
            print("\nEnviando mensaje con imagen...")
            
            # Crear cliente
            messaging_client = NotificationMessagesClient.from_connection_string(self.connection_string)
            
            # URL de imagen de prueba
            input_media_uri = "https://aka.ms/acsicon1"
            
            # Configurar mensaje con imagen
            image_message_options = ImageNotificationContent(
                channel_registration_id=self.channel_registration_id,
                to=[self.recipient_number],
                media_uri=input_media_uri
            )
            
            # Enviar mensaje
            message_responses = messaging_client.send(image_message_options)
            response = message_responses.receipts[0]
            
            if response is not None:
                print(f"EXITO - Mensaje con imagen enviado correctamente")
                print(f"  Message ID: {response.message_id}")
                print(f"  To: {response.to}")
                return True
            else:
                print("ERROR - El mensaje con imagen falló al enviar")
                return False
                
        except Exception as e:
            print(f"ERROR - Error enviando mensaje con imagen: {e}")
            return False
    
    def send_document_message(self):
        """Envía un mensaje con documento usando el SDK oficial"""
        try:
            from azure.communication.messages import NotificationMessagesClient
            from azure.communication.messages.models import DocumentNotificationContent
            
            print("\nEnviando mensaje con documento...")
            
            # Crear cliente
            messaging_client = NotificationMessagesClient.from_connection_string(self.connection_string)
            
            # URL de documento de prueba (placeholder)
            input_media_uri = "https://example.com/document.pdf"
            
            # Configurar mensaje con documento
            document_options = DocumentNotificationContent(
                channel_registration_id=self.channel_registration_id,
                to=[self.recipient_number],
                caption="Documento de ejemplo enviado desde VEA Connect",
                file_name="documento_ejemplo.pdf",
                media_uri=input_media_uri
            )
            
            # Enviar mensaje
            message_responses = messaging_client.send(document_options)
            response = message_responses.receipts[0]
            
            if response is not None:
                print(f"EXITO - Mensaje con documento enviado correctamente")
                print(f"  Message ID: {response.message_id}")
                print(f"  To: {response.to}")
                return True
            else:
                print("ERROR - El mensaje con documento falló al enviar")
                return False
                
        except Exception as e:
            print(f"ERROR - Error enviando mensaje con documento: {e}")
            return False
    
    def send_template_message(self):
        """Envía un mensaje de plantilla usando el SDK oficial"""
        try:
            from azure.communication.messages import NotificationMessagesClient
            from azure.communication.messages.models import TemplateNotificationContent, MessageTemplate
            
            print("\nEnviando mensaje de plantilla...")
            
            # Crear cliente
            messaging_client = NotificationMessagesClient.from_connection_string(self.connection_string)
            
            # Configurar plantilla (reemplazar con tu plantilla real)
            input_template = MessageTemplate(
                name="hello_world",  # Reemplazar con nombre real de tu plantilla
                language="es"
            )
            
            # Configurar mensaje de plantilla
            template_options = TemplateNotificationContent(
                channel_registration_id=self.channel_registration_id,
                to=[self.recipient_number],
                template=input_template
            )
            
            # Enviar mensaje
            message_responses = messaging_client.send(template_options)
            response = message_responses.receipts[0]
            
            if response is not None:
                print(f"EXITO - Mensaje de plantilla enviado correctamente")
                print(f"  Message ID: {response.message_id}")
                print(f"  To: {response.to}")
                return True
            else:
                print("ERROR - El mensaje de plantilla falló al enviar")
                return False
                
        except Exception as e:
            print(f"ERROR - Error enviando mensaje de plantilla: {e}")
            return False
    
    def test_connection(self):
        """Prueba la conexión básica"""
        try:
            from azure.communication.messages import NotificationMessagesClient
            
            print("\nProbando conexión con el SDK...")
            
            # Crear cliente
            messaging_client = NotificationMessagesClient.from_connection_string(self.connection_string)
            
            print("EXITO - Cliente creado correctamente")
            return True
            
        except Exception as e:
            print(f"ERROR - Error creando cliente: {e}")
            return False

def main():
    """Función principal"""
    print("EJEMPLO COMPLETO DE WHATSAPP CON SDK OFICIAL")
    print("=" * 50)
    
    # Cargar variables locales
    if not load_local_settings():
        print("No se pudieron cargar las variables locales")
        return False
    
    # Crear instancia de ejemplo
    example = WhatsAppAdvancedMessagesExample()
    
    # Verificar configuración
    if not example.connection_string or not example.channel_registration_id:
        print("ERROR - Faltan variables de configuración requeridas")
        return False
    
    # Probar conexión
    if not example.test_connection():
        return False
    
    # Probar diferentes tipos de mensajes
    success_text = example.send_text_message()
    success_image = example.send_image_message()
    success_document = example.send_document_message()
    success_template = example.send_template_message()
    
    # Resumen
    print(f"\nRESUMEN:")
    print("=" * 30)
    
    total_tests = 4
    successful_tests = sum([success_text, success_image, success_document, success_template])
    
    if successful_tests == total_tests:
        print("EXITO - Todos los mensajes se enviaron correctamente")
        print("El SDK oficial está funcionando perfectamente!")
        return True
    elif successful_tests > 0:
        print(f"PARCIAL - {successful_tests}/{total_tests} mensajes funcionaron")
        print("Algunos tipos de mensaje pueden requerir configuración adicional")
        return True
    else:
        print("ERROR - Ningún mensaje se pudo enviar")
        print("Posibles problemas:")
        print("  1. El SDK no está instalado")
        print("  2. Las variables de entorno son incorrectas")
        print("  3. El canal de WhatsApp no está configurado correctamente")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nEjemplo completado exitosamente")
    else:
        print("\nEjemplo falló")
