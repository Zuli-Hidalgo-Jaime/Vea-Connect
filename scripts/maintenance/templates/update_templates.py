#!/usr/bin/env python3
"""
Script to update WhatsApp templates with real ACS data.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.whatsapp_bot.models import WhatsAppTemplate

def update_templates():
    """Update templates with real ACS data."""
    
    # Template configurations with real ACS data
    templates_data = [
        {
            'template_name': 'vea_info_donativos',
            'template_id': 'vea_info_donativos',
            'channel_id': 'c3dd072b-92b3-4812-8ed0-10b1d3a45da1',
            'language': 'es_MX',
            'category': 'donations',
            'parameters': [
                'customer_name',
                'ministry_name', 
                'bank_name',
                'beneficiary_name',
                'account_number',
                'clabe_number',
                'contact_name',
                'contact_phone'
            ]
        },
        {
            'template_name': 'vea_event_info',
            'template_id': 'vea_event_info',
            'channel_id': 'c3dd072b-92b3-4812-8ed0-10b1d3a45da1',
            'language': 'es_MX',
            'category': 'events',
            'parameters': [
                'customer_name',
                'event_name',
                'event_date',
                'event_location'
            ]
        },
        {
            'template_name': 'vea_contacto_ministerio',
            'template_id': 'vea_contacto_ministerio',
            'channel_id': 'c3dd072b-92b3-4812-8ed0-10b1d3a45da1',
            'language': 'es_MX',
            'category': 'ministry',
            'parameters': [
                'customer_name',
                'ministry_name',
                'contact_name',
                'contact_phone'
            ]
        },
        {
            'template_name': 'vea_request_received',
            'template_id': 'vea_request_received',
            'channel_id': 'c3dd072b-92b3-4812-8ed0-10b1d3a45da1',
            'language': 'es_MX',
            'category': 'general',
            'parameters': [
                'customer_name',
                'request_summary'
            ]
        }
    ]
    
    print("🔄 Updating WhatsApp templates with real ACS data...")
    
    # Delete existing templates
    WhatsAppTemplate.objects.all().delete()
    print("✅ Existing templates deleted")
    
    # Create new templates
    for template_data in templates_data:
        template = WhatsAppTemplate.objects.create(
            template_name=template_data['template_name'],
            template_id=template_data['template_id'],
            channel_id=template_data['channel_id'],
            language=template_data['language'],
            category=template_data['category'],
            parameters=template_data['parameters'],
            is_active=True
        )
        print(f"✅ Created template: {template.template_name} ({template.category})")
    
    print(f"\n🎉 Successfully updated {len(templates_data)} templates!")
    
    # Display summary
    print("\n📋 Template Summary:")
    print("-" * 50)
    for template in WhatsAppTemplate.objects.all():
        print(f"• {template.template_name}: {template.category} ({len(template.parameters)} parameters)")
        print(f"  Channel ID: {template.channel_id}")
        print(f"  Language: {template.language}")
        print()

if __name__ == '__main__':
    update_templates() 