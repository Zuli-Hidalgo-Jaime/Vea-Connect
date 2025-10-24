#!/usr/bin/env python
"""
Final system integration test
"""
import os
import sys
import django  # pyright: reportMissingImports=false
from django.test import TestCase
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
django.setup()

# Configure environment variables for tests
os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'test_connection_string'
os.environ['AZURE_STORAGE_CONTAINER'] = 'test_container'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
os.environ['AZURE_OPENAI_API_KEY'] = 'test_key'
os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT'] = 'test_chat'
os.environ['AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT'] = 'test_embeddings'


class FinalSystemTest(TestCase):
    """Final system integration test"""

    def test_system_health(self):
        """Test overall system health"""
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_settings_loaded(self):
        """Test that settings are loaded correctly"""
        self.assertTrue(hasattr(settings, 'DATABASES'))
        self.assertTrue(hasattr(settings, 'INSTALLED_APPS'))

    def test_apps_installed(self):
        """Test that all required apps are installed"""
        required_apps = [
            'apps.core',
            'apps.directory', 
            'apps.documents',
            'apps.events',
            'apps.donations',
            'apps.embeddings',
            'apps.whatsapp_bot'
        ]
        
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_environment_variables(self):
        """Test that environment variables are set"""
        required_vars = [
            'AZURE_STORAGE_CONNECTION_STRING',
            'AZURE_STORAGE_CONTAINER',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY'
        ]
        
        for var in required_vars:
            self.assertIsNotNone(os.getenv(var)) 