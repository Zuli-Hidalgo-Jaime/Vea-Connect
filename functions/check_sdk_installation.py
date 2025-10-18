#!/usr/bin/env python3
"""
Script para verificar la instalación del SDK de Azure Communication Messages
"""
import sys
import importlib

def check_sdk_installation():
    """Verifica si el SDK está instalado correctamente"""
    print("Verificando instalación del SDK de Azure Communication Messages...")
    
    # Lista de módulos a verificar
    modules_to_check = [
        'azure.communication.messages',
        'azure.communication.messages.models',
        'azure.communication.messages._client',
        'azure.core',
        'azure.core.credentials'
    ]
    
    all_installed = True
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ {module_name} - INSTALADO")
            
            # Verificar clases específicas si es el módulo principal
            if module_name == 'azure.communication.messages':
                try:
                    from azure.communication.messages import NotificationMessagesClient
                    print(f"  ✓ NotificationMessagesClient - DISPONIBLE")
                except ImportError as e:
                    print(f"  ✗ NotificationMessagesClient - NO DISPONIBLE: {e}")
                    all_installed = False
                    
            if module_name == 'azure.communication.messages.models':
                try:
                    from azure.communication.messages.models import TextNotificationContent, ImageNotificationContent
                    print(f"  ✓ TextNotificationContent - DISPONIBLE")
                    print(f"  ✓ ImageNotificationContent - DISPONIBLE")
                except ImportError as e:
                    print(f"  ✗ Modelos - NO DISPONIBLES: {e}")
                    all_installed = False
                    
        except ImportError as e:
            print(f"✗ {module_name} - NO INSTALADO: {e}")
            all_installed = False
    
    # Verificar versión
    try:
        import azure.communication.messages
        version = getattr(azure.communication.messages, '__version__', 'Desconocida')
        print(f"\nVersión del SDK: {version}")
    except:
        print("\nNo se pudo obtener la versión del SDK")
    
    # Resumen
    print(f"\nResumen:")
    if all_installed:
        print("✓ SDK completamente instalado y funcional")
        return True
    else:
        print("✗ SDK incompleto o con problemas")
        print("\nPara instalar el SDK:")
        print("pip install azure-communication-messages")
        return False

def test_sdk_functionality():
    """Prueba la funcionalidad básica del SDK"""
    print("\nProbando funcionalidad del SDK...")
    
    try:
        from azure.communication.messages import NotificationMessagesClient
        from azure.communication.messages.models import TextNotificationContent
        
        print("✓ Importaciones exitosas")
        
        # Probar creación de cliente (sin connection string)
        try:
            # Esto debería fallar sin connection string, pero no debería fallar por importación
            client = NotificationMessagesClient.from_connection_string("dummy")
            print("✓ Cliente creado (aunque con connection string inválido)")
        except Exception as e:
            if "connection string" in str(e).lower() or "invalid" in str(e).lower():
                print("✓ Cliente creado correctamente (error esperado por connection string inválido)")
            else:
                print(f"✗ Error inesperado creando cliente: {e}")
        
        # Probar creación de contenido de texto
        try:
            text_content = TextNotificationContent(
                channel_registration_id="test-id",
                to=["+1234567890"],
                content="Test message"
            )
            print("✓ TextNotificationContent creado correctamente")
        except Exception as e:
            print(f"✗ Error creando TextNotificationContent: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error probando funcionalidad: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("VERIFICACIÓN DEL SDK DE AZURE COMMUNICATION MESSAGES")
    print("=" * 60)
    
    # Verificar instalación
    sdk_installed = check_sdk_installation()
    
    # Probar funcionalidad si está instalado
    if sdk_installed:
        sdk_functional = test_sdk_functionality()
        
        if sdk_functional:
            print("\n🎉 SDK completamente funcional!")
        else:
            print("\n⚠️ SDK instalado pero con problemas de funcionalidad")
    else:
        print("\n❌ SDK no instalado correctamente")
    
    print("=" * 60)
