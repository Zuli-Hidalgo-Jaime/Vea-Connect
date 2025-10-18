#!/usr/bin/env python3
"""
WhatsApp Event Grid Probe Script

This script simulates ACS Advanced Messaging events to test the WhatsApp webhook
without actually sending messages. It displays parsed text and sender information.
"""

import json
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, Any, List

# Add functions directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions'))

try:
    from helpers import extract_incoming_text
except ImportError:
    print("Warning: Could not import helpers module. Using fallback parser.")
    
    def extract_incoming_text(event_payload: Dict[str, Any]) -> tuple:
        """Fallback parser for testing."""
        data = event_payload.get('data', {})
        
        # Simple fallback parsing
        if 'messageBody' in data and 'from' in data:
            return data.get('from', ''), data.get('messageBody', ''), {'schema_used': 'fallback'}
        
        return "", "", {'schema_used': 'unknown', 'errors': ['No valid schema found']}


def create_test_payloads() -> List[Dict[str, Any]]:
    """
    Create test payloads for different ACS schemas.
    
    Returns:
        List of test payloads
    """
    base_event = {
        "id": "test-event-id",
        "eventType": "Microsoft.Communication.AdvancedMessageReceived",
        "subject": "test-subject",
        "eventTime": datetime.utcnow().isoformat(),
        "dataVersion": "1.0"
    }
    
    test_payloads = [
        # Schema 1: Legacy format
        {
            **base_event,
            "data": {
                "messageBody": "Hola, necesito información sobre donaciones",
                "from": "+525512345678"
            }
        },
        
        # Schema 2: Standard format
        {
            **base_event,
            "data": {
                "message": {
                    "content": {
                        "text": "¿Cuáles son los horarios de atención?"
                    },
                    "from": {
                        "phoneNumber": "+525598765432"
                    }
                }
            }
        },
        
        # Schema 3: Alternative format (content with text)
        {
            **base_event,
            "data": {
                "content": {
                    "text": "Quiero hacer una donación en especie"
                },
                "from": "+525511112222"
            }
        },
        
        # Schema 4: Alternative format (content with body)
        {
            **base_event,
            "data": {
                "content": {
                    "body": "¿Tienen eventos próximos?"
                },
                "from": "+525533334444"
            }
        },
        
        # Schema 5: Direct text
        {
            **base_event,
            "data": {
                "text": "Necesito contactar al equipo de VEA Connect",
                "from": "+525555556666"
            }
        },
        
        # Invalid payload for testing error handling
        {
            **base_event,
            "data": {
                "unknown_field": "This should not parse"
            }
        }
    ]
    
    return test_payloads


def test_payload_parsing(payload: Dict[str, Any], payload_name: str) -> None:
    """
    Test parsing of a single payload.
    
    Args:
        payload: Event payload to test
        payload_name: Name/description of the payload
    """
    print(f"\n{'='*60}")
    print(f"Testing: {payload_name}")
    print(f"{'='*60}")
    
    try:
        # Extract text and sender
        sender, text, meta = extract_incoming_text(payload)
        
        print(f"📱 Sender: {sender}")
        print(f"💬 Text: {text}")
        print(f"🔧 Schema used: {meta.get('schema_used', 'unknown')}")
        print(f"✅ Parsing success: {meta.get('parsing_success', False)}")
        
        if meta.get('errors'):
            print(f"❌ Errors: {meta['errors']}")
        
        # Validate phone number format
        if sender:
            if sender.startswith('+') and len(sender) >= 10:
                print(f"✅ Phone number format: Valid E.164 ({sender})")
            else:
                print(f"⚠️ Phone number format: May need normalization ({sender})")
        else:
            print("❌ Phone number: Not found")
        
        # Validate text content
        if text and len(text.strip()) > 0:
            print(f"✅ Text content: Valid ({len(text)} characters)")
        else:
            print("❌ Text content: Empty or missing")
            
    except Exception as e:
        print(f"❌ Error parsing payload: {e}")


def simulate_event_grid_event(payload: Dict[str, Any]) -> None:
    """
    Simulate a complete Event Grid event.
    
    Args:
        payload: Event payload to simulate
    """
    print(f"\n{'='*60}")
    print("Simulating Event Grid Event")
    print(f"{'='*60}")
    
    # Create Event Grid event structure
    event = {
        "id": payload.get("id", "test-event-id"),
        "eventType": payload.get("eventType", "Microsoft.Communication.AdvancedMessageReceived"),
        "subject": payload.get("subject", "test-subject"),
        "eventTime": payload.get("eventTime", datetime.utcnow().isoformat()),
        "dataVersion": payload.get("dataVersion", "1.0"),
        "data": payload.get("data", {})
    }
    
    print(f"Event ID: {event['id']}")
    print(f"Event Type: {event['eventType']}")
    print(f"Subject: {event['subject']}")
    print(f"Event Time: {event['eventTime']}")
    print(f"Data Version: {event['dataVersion']}")
    
    # Test parsing
    sender, text, meta = extract_incoming_text(event)
    
    print(f"\n📱 Parsed Sender: {sender}")
    print(f"💬 Parsed Text: {text}")
    print(f"🔧 Schema Used: {meta.get('schema_used', 'unknown')}")
    print(f"✅ Success: {meta.get('parsing_success', False)}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="WhatsApp Event Grid Probe")
    parser.add_argument(
        "--payload", 
        type=str, 
        help="Custom payload JSON file to test"
    )
    parser.add_argument(
        "--schema", 
        type=int, 
        choices=[1, 2, 3, 4, 5], 
        help="Test specific schema (1-5)"
    )
    parser.add_argument(
        "--simulate", 
        action="store_true", 
        help="Simulate complete Event Grid event"
    )
    parser.add_argument(
        "--custom-text", 
        type=str, 
        help="Custom text to use in test payload"
    )
    parser.add_argument(
        "--custom-phone", 
        type=str, 
        help="Custom phone number to use in test payload"
    )
    
    args = parser.parse_args()
    
    print("🚀 WhatsApp Event Grid Probe")
    print("=" * 60)
    
    if args.payload:
        # Test custom payload from file
        try:
            with open(args.payload, 'r', encoding='utf-8') as f:
                custom_payload = json.load(f)
            test_payload_parsing(custom_payload, f"Custom payload from {args.payload}")
        except Exception as e:
            print(f"❌ Error loading custom payload: {e}")
            return 1
    else:
        # Test predefined payloads
        test_payloads = create_test_payloads()
        
        if args.schema:
            # Test specific schema
            if 1 <= args.schema <= len(test_payloads):
                payload = test_payloads[args.schema - 1]
                
                # Override with custom values if provided
                if args.custom_text:
                    if 'data' in payload and 'messageBody' in payload['data']:
                        payload['data']['messageBody'] = args.custom_text
                    elif 'data' in payload and 'message' in payload['data']:
                        payload['data']['message']['content']['text'] = args.custom_text
                    elif 'data' in payload and 'content' in payload['data']:
                        payload['data']['content']['text'] = args.custom_text
                    elif 'data' in payload and 'text' in payload['data']:
                        payload['data']['text'] = args.custom_text
                
                if args.custom_phone:
                    if 'data' in payload and 'from' in payload['data']:
                        payload['data']['from'] = args.custom_phone
                    elif 'data' in payload and 'message' in payload['data']:
                        payload['data']['message']['from']['phoneNumber'] = args.custom_phone
                
                test_payload_parsing(payload, f"Schema {args.schema}")
                
                if args.simulate:
                    simulate_event_grid_event(payload)
            else:
                print(f"❌ Invalid schema number. Available: 1-{len(test_payloads)}")
                return 1
        else:
            # Test all payloads
            for i, payload in enumerate(test_payloads, 1):
                test_payload_parsing(payload, f"Schema {i}")
    
    print(f"\n{'='*60}")
    print("✅ Probe completed successfully")
    print(f"{'='*60}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
