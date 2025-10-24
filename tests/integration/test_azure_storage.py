"""
Integration tests for Azure Storage service.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from django.test import TestCase
from django.conf import settings

from services.storage_service import AzureStorageService, azure_storage


class TestAzureStorageService(TestCase):
    """Test cases for Azure Storage service."""

    def setUp(self):
        """Set up test environment."""
        self.service = AzureStorageService()

    def test_service_initialization(self):
        """Test service initialization."""
        # Test that service can be initialized
        self.assertIsInstance(self.service, AzureStorageService)
        
        # Test configuration status
        status = self.service.get_configuration_status()
        self.assertIsInstance(status, dict)
        self.assertIn('connection_string_configured', status)
        self.assertIn('account_name_configured', status)
        self.assertIn('account_key_configured', status)
        self.assertIn('container_name', status)
        self.assertIn('client_initialized', status)

    def test_get_setting_fallback(self):
        """Test setting retrieval with fallback to environment variables."""
        # Test with environment variable fallback
        with patch.dict('os.environ', {'TEST_STORAGE_SETTING': 'env_value'}):
            value = self.service._get_setting('TEST_STORAGE_SETTING')
            self.assertEqual(value, 'env_value')
        
        # Test with default value
        value = self.service._get_setting('NONEXISTENT_SETTING', 'default_value')
        self.assertEqual(value, 'default_value')

    def test_upload_file_without_client(self):
        """Test upload file when Azure Storage client is not initialized."""
        # Test upload without client
        result = self.service.upload_file(
            file_path="/tmp/test.txt",
            blob_name="test.txt"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Azure Storage client not initialized', result['error'])

    def test_upload_data_without_client(self):
        """Test upload data when Azure Storage client is not initialized."""
        # Test upload data without client
        result = self.service.upload_data(
            data=b"test data",
            blob_name="test.txt"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Azure Storage client not initialized', result['error'])

    def test_download_file_without_client(self):
        """Test download file when Azure Storage client is not initialized."""
        # Test download without client
        result = self.service.download_file(
            blob_name="test.txt",
            local_path="/tmp/test.txt"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Azure Storage client not initialized', result['error'])

    def test_get_blob_url_without_client(self):
        """Test get blob URL when Azure Storage client is not initialized."""
        # Test get URL without client
        result = self.service.get_blob_url(
            blob_name="test.txt"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Azure Storage client not initialized', result['error'])

    def test_delete_blob_without_client(self):
        """Test delete blob when Azure Storage client is not initialized."""
        # Test delete without client
        result = self.service.delete_blob(
            blob_name="test.txt"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Azure Storage client not initialized', result['error'])

    def test_list_blobs_without_client(self):
        """Test list blobs when Azure Storage client is not initialized."""
        # Test list without client
        result = self.service.list_blobs()
        
        self.assertFalse(result['success'])
        self.assertIn('Azure Storage client not initialized', result['error'])

    def test_blob_exists_without_client(self):
        """Test blob exists when Azure Storage client is not initialized."""
        # Test exists check without client
        result = self.service.blob_exists(
            blob_name="test.txt"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Azure Storage client not initialized', result['error'])

    @patch('azure.storage.blob.BlobServiceClient')
    def test_service_with_mocked_client(self, mock_blob_service):
        """Test service with mocked Azure Storage client."""
        # Mock the BlobServiceClient
        mock_client = MagicMock()
        mock_blob_service.from_connection_string.return_value = mock_client
        
        # Create service with connection string
        with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'}):
            service = AzureStorageService()
            
            # Test that client is initialized
            status = service.get_configuration_status()
            self.assertTrue(status['client_initialized'])

    @patch('azure.storage.blob.BlobServiceClient')
    def test_upload_file_with_mocked_client(self, mock_blob_service):
        """Test upload file with mocked client."""
        # Mock the BlobServiceClient and blob client
        mock_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client
        
        # Mock file operations
        test_data = b"test file content"
        with patch('builtins.open', mock_open(read_data=test_data)):
            with patch('os.path.getsize', return_value=len(test_data)):
                with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'}):
                    service = AzureStorageService()
                    
                    # Test upload
                    result = service.upload_file(
                        file_path="/tmp/test.txt",
                        blob_name="test.txt"
                    )
                    
                    self.assertTrue(result['success'])
                    self.assertEqual(result['blob_name'], 'test.txt')
                    self.assertEqual(result['size'], len(test_data))

    @patch('azure.storage.blob.BlobServiceClient')
    def test_upload_data_with_mocked_client(self, mock_blob_service):
        """Test upload data with mocked client."""
        # Mock the BlobServiceClient and blob client
        mock_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client
        
        # Test data
        test_data = b"test data content"
        
        with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'}):
            service = AzureStorageService()
            
            # Test upload
            result = service.upload_data(
                data=test_data,
                blob_name="test.txt"
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['blob_name'], 'test.txt')
            self.assertEqual(result['size'], len(test_data))

    @patch('azure.storage.blob.BlobServiceClient')
    def test_download_file_with_mocked_client(self, mock_blob_service):
        """Test download file with mocked client."""
        # Mock the BlobServiceClient and blob client
        mock_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client
        
        # Mock download stream
        mock_download_stream = MagicMock()
        mock_download_stream.readall.return_value = b"downloaded content"
        mock_blob_client.download_blob.return_value = mock_download_stream
        
        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.getsize', return_value=18):
                with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'}):
                    service = AzureStorageService()
                    
                    # Test download
                    result = service.download_file(
                        blob_name="test.txt",
                        local_path="/tmp/test.txt"
                    )
                    
                    self.assertTrue(result['success'])
                    self.assertEqual(result['blob_name'], 'test.txt')
                    self.assertEqual(result['size'], 18)

    @patch('azure.storage.blob.BlobServiceClient')
    def test_get_blob_url_with_mocked_client(self, mock_blob_service):
        """Test get blob URL with mocked client."""
        # Mock the BlobServiceClient and blob client
        mock_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client
        
        # Mock SAS token generation
        mock_blob_client.generate_sas.return_value = "test_sas_token"
        mock_blob_client.url = "https://test.blob.core.windows.net/container/test.txt"
        
        with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'}):
            service = AzureStorageService()
            
            # Test get URL
            result = service.get_blob_url(
                blob_name="test.txt"
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['blob_name'], 'test.txt')
            self.assertIn('signed_url', result)

    @patch('azure.storage.blob.BlobServiceClient')
    def test_list_blobs_with_mocked_client(self, mock_blob_service):
        """Test list blobs with mocked client."""
        # Mock the BlobServiceClient and container client
        mock_client = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_service.from_connection_string.return_value = mock_client
        mock_client.get_container_client.return_value = mock_container_client
        
        # Mock blob list
        mock_blob = MagicMock()
        mock_blob.name = "test.txt"
        mock_blob.size = 1024
        mock_blob.last_modified = None
        mock_blob.content_settings = MagicMock()
        mock_blob.content_settings.content_type = "text/plain"
        
        mock_container_client.list_blobs.return_value = [mock_blob]
        
        with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'}):
            service = AzureStorageService()
            
            # Test list blobs
            result = service.list_blobs()
            
            self.assertTrue(result['success'])
            self.assertEqual(result['count'], 1)
            self.assertEqual(len(result['blobs']), 1)
            self.assertEqual(result['blobs'][0]['name'], 'test.txt')

    @patch('azure.storage.blob.BlobServiceClient')
    def test_blob_exists_with_mocked_client(self, mock_blob_service):
        """Test blob exists with mocked client."""
        # Mock the BlobServiceClient and blob client
        mock_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client
        
        # Mock exists check
        mock_blob_client.exists.return_value = True
        
        with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'}):
            service = AzureStorageService()
            
            # Test exists check
            result = service.blob_exists(
                blob_name="test.txt"
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['blob_name'], 'test.txt')
            self.assertTrue(result['exists'])


class TestAzureStorageIntegration(TestCase):
    """Integration tests for Azure Storage with real components."""

    def test_global_instance(self):
        """Test the global Azure Storage instance."""
        # Test that global instance exists
        self.assertIsInstance(azure_storage, AzureStorageService)
        
        # Test configuration status
        status = azure_storage.get_configuration_status()
        self.assertIsInstance(status, dict)

    def test_error_handling(self):
        """Test error handling in Azure Storage service."""
        # Test that service handles errors gracefully
        try:
            # Test with invalid parameters
            azure_storage.upload_file("", "")
            azure_storage.upload_data(b"", "")
            azure_storage.download_file("", "")
            azure_storage.get_blob_url("")
            azure_storage.delete_blob("")
            azure_storage.list_blobs()
            azure_storage.blob_exists("")
        except Exception as e:
            self.fail(f"Service should handle invalid parameters gracefully: {e}")

    def test_container_name_default(self):
        """Test default container name configuration."""
        # Test that default container name is set
        self.assertEqual(azure_storage.container_name, 'vea-connect-files')

    def test_connection_string_parsing(self):
        """Test connection string parsing."""
        # Test with valid connection string format
        test_connection_string = "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey;EndpointSuffix=core.windows.net"
        
        with patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': test_connection_string}):
            service = AzureStorageService()
            status = service.get_configuration_status()
            
            # Should detect connection string
            self.assertTrue(status['connection_string_configured'])

    def test_account_credentials_parsing(self):
        """Test account credentials parsing."""
        # Test with account name and key
        with patch.dict('os.environ', {
            'AZURE_STORAGE_ACCOUNT_NAME': 'testaccount',
            'AZURE_STORAGE_ACCOUNT_KEY': 'testkey'
        }):
            service = AzureStorageService()
            status = service.get_configuration_status()
            
            # Should detect account credentials
            self.assertTrue(status['account_name_configured'])
            self.assertTrue(status['account_key_configured'])


@pytest.mark.integration
class TestAzureStorageProduction(TestCase):
    """Production-like tests for Azure Storage."""

    def test_production_configuration(self):
        """Test production configuration scenarios."""
        # Test with production-like settings
        with patch.dict('os.environ', {
            'AZURE_STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=prodaccount;AccountKey=prodkey;EndpointSuffix=core.windows.net',
            'AZURE_STORAGE_CONTAINER_NAME': 'prod-container'
        }):
            service = AzureStorageService()
            status = service.get_configuration_status()
            
            # In production, we expect these to be configured
            self.assertTrue(status['connection_string_configured'])
            self.assertEqual(status['container_name'], 'prod-container')

    def test_large_file_handling(self):
        """Test handling of large files."""
        # Create a temporary file with some content
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Large file content for testing")
            temp_file_path = temp_file.name
        
        try:
            # Test that service can handle file operations
            result = azure_storage.upload_file(
                file_path=temp_file_path,
                blob_name="large_test_file.txt"
            )
            
            # Should handle gracefully (even if not configured)
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_concurrent_operations(self):
        """Test concurrent storage operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def storage_operation(thread_id):
            try:
                # Test different operations
                test_data = f"test_data_{thread_id}".encode()
                
                # Upload data
                result = azure_storage.upload_data(
                    data=test_data,
                    blob_name=f"concurrent_test_{thread_id}.txt"
                )
                results.append(result)
                
                # Check if blob exists
                result = azure_storage.blob_exists(
                    blob_name=f"concurrent_test_{thread_id}.txt"
                )
                results.append(result)
                
                time.sleep(0.01)  # Small delay
                
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=storage_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent operations produced errors: {errors}")
        self.assertEqual(len(results), 10, "All operations should complete")
        
        # All operations should return valid results (even if not successful due to no client)
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
