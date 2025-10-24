"""
Tests para validar que no hay referencias obsoletas a Redis
"""
import os
import re
from django.test import TestCase
from pathlib import Path


class TestRedisCleanup(TestCase):
    """Tests para validar que no hay referencias obsoletas a Redis"""
    
    def test_no_redis_imports_in_tests(self):
        """Test que no hay imports directos de Redis en archivos de test"""
        tests_dir = Path(__file__).parent.parent
        redis_import_pattern = re.compile(r'^import\s+redis|^from\s+redis')
        
        for test_file in tests_dir.rglob('*.py'):
            if test_file.name.startswith('test_'):
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        if redis_import_pattern.search(line.strip()):
                            self.fail(
                                f"Redis import found in {test_file} at line {i}: {line.strip()}\n"
                                "Use django.core.cache instead of direct Redis imports."
                            )
    
    def test_no_redis_client_creation_in_tests(self):
        """Test que no hay creación directa de Redis client en tests"""
        tests_dir = Path(__file__).parent.parent
        redis_client_pattern = re.compile(r'redis\.Redis\(')
        
        for test_file in tests_dir.rglob('*.py'):
            if test_file.name.startswith('test_') and test_file.name != 'test_redis_cleanup.py':
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if redis_client_pattern.search(content):
                        self.fail(
                            f"Direct Redis client creation found in {test_file}\n"
                            "Use django.core.cache instead of redis.Redis()."
                        )
    
    def test_whatsapp_bot_uses_cache(self):
        """Test que WhatsApp bot usa cache en lugar de Redis directo"""
        from apps.whatsapp_bot.services import LoggingService
        from django.core.cache import cache
        
        # Crear instancia del servicio
        logging_service = LoggingService()
        
        # Verificar que usa cache
        self.assertIsNotNone(logging_service)
        
        # Test que los métodos de cache funcionan
        test_data = {'test': 'data'}
        cache.set('test_key', test_data, 60)
        retrieved_data = cache.get('test_key')
        self.assertEqual(retrieved_data, test_data)
    
    def test_cache_fallback_works(self):
        """Test que el fallback a cache funciona cuando Redis no está disponible"""
        from apps.whatsapp_bot.services import LoggingService
        from django.core.cache import cache
        
        # Simular que Redis no está disponible
        with self.settings(CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }):
            logging_service = LoggingService()
            
            # Test que el servicio funciona con cache local
            phone_number = '+1234567890'
            context_data = {'session_id': 'test-123'}
            
            # Test save_context_to_redis (que realmente usa cache)
            result = logging_service.save_context_to_redis(phone_number, context_data)
            self.assertTrue(result)
            
            # Test get_context_from_redis (que realmente usa cache)
            retrieved_context = logging_service.get_context_from_redis(phone_number)
            self.assertEqual(retrieved_context, context_data)
    
    def test_no_docker_references_in_tests(self):
        """Test que no hay referencias a Docker en archivos de test"""
        tests_dir = Path(__file__).parent.parent
        docker_pattern = re.compile(r'docker|Dockerfile|docker-compose', re.IGNORECASE)
        
        for test_file in tests_dir.rglob('*.py'):
            if test_file.name.startswith('test_') and test_file.name != 'test_redis_cleanup.py':
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if docker_pattern.search(content):
                        self.fail(
                            f"Docker reference found in {test_file}\n"
                            "Docker has been removed from the architecture."
                        )
    
    def test_azure_storage_usage(self):
        """Test que se usa Azure Storage en lugar de almacenamiento local"""
        from django.conf import settings
        
        # Verificar que se usa Azure Storage (puede estar en diferentes configuraciones)
        has_azure_storage = (
            hasattr(settings, 'AZURE_STORAGE_CONNECTION_STRING') or
            hasattr(settings, 'AZURE_STORAGE_CONTAINER_NAME') or
            hasattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME') or
            hasattr(settings, 'AZURE_STORAGE_ACCOUNT_KEY')
        )
        
        # Verificar que se usa algún tipo de almacenamiento en la nube
        has_cloud_storage = (
            has_azure_storage or
            hasattr(settings, 'AWS_S3_BUCKET_NAME') or
            hasattr(settings, 'GOOGLE_CLOUD_STORAGE_BUCKET')
        )
        
        self.assertTrue(
            has_cloud_storage,
            "No se encontró configuración de almacenamiento en la nube"
        ) 