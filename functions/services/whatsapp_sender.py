import os
import logging
from typing import Optional

# Lazy loading of SMS client
_sms_client = None

def get_sms_client():
    """Get SMS client with lazy loading to avoid import errors."""
    global _sms_client
    if _sms_client is None:
        try:
            from azure.communication.sms import SmsClient
            from utils.env_utils import get_env
            
            # Get connection string
            connection_string = get_env("AZURE_COMMUNICATION_CONNECTION_STRING")
            
            _sms_client = SmsClient.from_connection_string(connection_string)
        except Exception as e:
            logging.error(f"Failed to initialize SMS client: {str(e)}")
            return None
    return _sms_client

def send_whatsapp_message(to_number: str, message: str, event_data: dict) -> bool:
    """
    Send WhatsApp message using Azure Communication Services
    
    Args:
        to_number: Phone number in format whatsapp:+1234567890
        message: Message to send
        event_data: Full event data to extract sender information
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        client = get_sms_client()
        if not client:
            logging.error("SMS client not available")
            return False
        
        # Extract phone number from whatsapp: format
        if to_number.startswith("whatsapp:"):
            phone_number = to_number.replace("whatsapp:", "")
        else:
            phone_number = to_number
        
        # Get sender phone from event data
        # Try different possible fields where the sender phone might be
        sender_phone = None
        
        # Check if there's a 'to' field in the event (the number that received the message)
        if "to" in event_data:
            sender_phone = event_data["to"]
            if sender_phone.startswith("whatsapp:"):
                sender_phone = sender_phone.replace("whatsapp:", "")
        # If no 'to' field, try to get from environment as fallback
        elif "WHATSAPP_SENDER_PHONE" in os.environ:
            from utils.env_utils import get_env
            sender_phone = get_env("WHATSAPP_SENDER_PHONE")
        else:
            logging.error("No sender phone found in event data or environment")
            return False
        
        logging.info(f"Sending message from {sender_phone} to {phone_number}")
        
        # Send message
        response = client.send(
            from_=sender_phone,
            to=[phone_number],
            message=message
        )
        
        logging.info(f"Message sent successfully to {to_number}")
        return True
        
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {str(e)}")
        return False
