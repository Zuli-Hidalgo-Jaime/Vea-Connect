"""
Unit tests for OpenAIService
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from apps.embeddings.openai_service import OpenAIService


class TestOpenAIService(unittest.TestCase):
    """Test cases for OpenAIService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear environment variables for clean tests
        self.env_vars_to_clear = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_CHAT_DEPLOYMENT',
            'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT',
            'AZURE_OPENAI_CHAT_API_VERSION',
            'AZURE_OPENAI_EMBEDDINGS_API_VERSION',
            'OPENAI_API_KEY'
        ]
        
        for var in self.env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up after tests."""
        for var in self.env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    def test_init_without_configuration(self):
        """Test initialization without Azure OpenAI configuration."""
        service = OpenAIService()
        
        assert service.client is None
        assert service.is_configured is False
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('apps.embeddings.openai_service.AzureOpenAI')
    def test_init_with_configuration(self, mock_azure_openai):
        """Test initialization with Azure OpenAI configuration."""
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client
        
        service = OpenAIService()
        
        assert service.client is not None
        assert service.is_configured is True
        mock_azure_openai.assert_called_once()
    
    def test_generate_embedding_without_config(self):
        """Test embedding generation without Azure OpenAI configuration."""
        service = OpenAIService()
        
        text = "Test text for embedding"
        embedding = service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_embedding_empty_text(self):
        """Test embedding generation with empty text."""
        service = OpenAIService()
        
        with self.assertRaises(ValueError):
            service.generate_embedding("")
        
        with self.assertRaises(ValueError):
            service.generate_embedding("   ")
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('apps.embeddings.openai_service.AzureOpenAI')
    def test_generate_embedding_with_config(self, mock_azure_openai):
        """Test embedding generation with Azure OpenAI configuration."""
        # Mock the Azure OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_client.embeddings.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client
        
        service = OpenAIService()
        
        text = "Test text for embedding"
        embedding = service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        mock_client.embeddings.create.assert_called_once()
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('apps.embeddings.openai_service.AzureOpenAI')
    def test_generate_embedding_fallback_on_error(self, mock_azure_openai):
        """Test embedding generation falls back to dummy on error."""
        # Mock the Azure OpenAI client to raise an exception
        mock_client = Mock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_azure_openai.return_value = mock_client
        
        service = OpenAIService()
        
        text = "Test text for embedding"
        embedding = service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_chat_response_without_config(self):
        """Test chat response generation without Azure OpenAI configuration."""
        service = OpenAIService()
        
        messages = [{"role": "user", "content": "Hello"}]
        response = service.generate_chat_response(messages)
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_generate_chat_response_empty_messages(self):
        """Test chat response generation with empty messages."""
        service = OpenAIService()
        
        with self.assertRaises(ValueError):
            service.generate_chat_response([])
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('apps.embeddings.openai_service.AzureOpenAI')
    def test_generate_chat_response_with_config(self, mock_azure_openai):
        """Test chat response generation with Azure OpenAI configuration."""
        # Mock the Azure OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        mock_client.chat.completions.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client
        
        service = OpenAIService()
        
        messages = [{"role": "user", "content": "Hello"}]
        response = service.generate_chat_response(messages)
        
        assert isinstance(response, str)
        assert response == "Hello! How can I help you?"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('apps.embeddings.openai_service.AzureOpenAI')
    def test_generate_chat_response_with_parameters(self, mock_azure_openai):
        """Test chat response generation with custom parameters."""
        # Mock the Azure OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Custom response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client
        
        service = OpenAIService()
        
        messages = [{"role": "user", "content": "Test"}]
        response = service.generate_chat_response(
            messages, 
            max_tokens=500, 
            temperature=0.5
        )
        
        assert isinstance(response, str)
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['max_tokens'] == 500
        assert call_args[1]['temperature'] == 0.5
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('apps.embeddings.openai_service.AzureOpenAI')
    def test_generate_chat_response_fallback_on_error(self, mock_azure_openai):
        """Test chat response generation falls back to dummy on error."""
        # Mock the Azure OpenAI client to raise an exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_azure_openai.return_value = mock_client
        
        service = OpenAIService()
        
        messages = [{"role": "user", "content": "Hello"}]
        response = service.generate_chat_response(messages)
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_get_configuration_status(self):
        """Test configuration status retrieval."""
        service = OpenAIService()
        
        status = service.get_configuration_status()
        
        assert isinstance(status, dict)
        assert 'is_configured' in status
        assert 'azure_endpoint' in status
        assert 'chat_deployment' in status
        assert 'embeddings_deployment' in status
        assert 'api_version' in status
        assert 'has_api_key' in status
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'AZURE_OPENAI_CHAT_API_VERSION': '2024-02-15-preview',
        'OPENAI_API_KEY': 'test-key'
    })
    def test_get_configuration_status_with_config(self):
        """Test configuration status with environment variables set."""
        service = OpenAIService()
        
        status = service.get_configuration_status()
        
        assert status['azure_endpoint'] == 'https://test.openai.azure.com/'
        assert status['chat_deployment'] == 'gpt-4'
        assert status['embeddings_deployment'] == 'text-embedding-ada-002'
        assert status['api_version'] == '2024-02-15-preview'
        assert status['has_api_key'] is True
    
    def test_test_connection_without_config(self):
        """Test connection test without configuration."""
        service = OpenAIService()
        
        results = service.test_connection()
        
        assert isinstance(results, dict)
        assert results['connection_test'] is False
        assert results['embedding_test'] is False
        assert results['chat_test'] is False
        assert len(results['errors']) > 0
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'test-key'
    })
    @patch('apps.embeddings.openai_service.AzureOpenAI')
    def test_test_connection_with_config(self, mock_azure_openai):
        """Test connection test with configuration."""
        # Mock the Azure OpenAI client
        mock_client = Mock()
        
        # Mock embedding response
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock()]
        mock_embedding_response.data[0].embedding = [0.1, 0.2, 0.3] * 512
        mock_client.embeddings.create.return_value = mock_embedding_response
        
        # Mock chat response
        mock_chat_response = Mock()
        mock_chat_response.choices = [Mock()]
        mock_chat_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_chat_response
        
        mock_azure_openai.return_value = mock_client
        
        service = OpenAIService()
        
        results = service.test_connection()
        
        assert isinstance(results, dict)
        assert results['connection_test'] is True
        assert results['embedding_test'] is True
        assert results['chat_test'] is True
        assert len(results['errors']) == 0
    
    def test_dummy_embedding_consistency(self):
        """Test that dummy embeddings are consistent for same input."""
        service = OpenAIService()
        
        text = "Test text for consistency"
        embedding1 = service._generate_dummy_embedding(text)
        embedding2 = service._generate_dummy_embedding(text)
        
        assert embedding1 == embedding2
        assert len(embedding1) == 1536
        assert all(isinstance(x, float) for x in embedding1)
    
    def test_dummy_chat_response_variety(self):
        """Test that dummy chat responses provide variety."""
        service = OpenAIService()
        
        messages = [{"role": "user", "content": "Hello"}]
        responses = set()
        
        # Generate multiple responses to check variety
        for _ in range(10):
            response = service._generate_dummy_chat_response(messages)
            responses.add(response)
        
        # Should have some variety (not all the same)
        assert len(responses) > 1
    
    def test_dummy_embedding_different_inputs(self):
        """Test that dummy embeddings are different for different inputs."""
        service = OpenAIService()
        
        text1 = "First test text"
        text2 = "Second test text"
        
        embedding1 = service._generate_dummy_embedding(text1)
        embedding2 = service._generate_dummy_embedding(text2)
        
        assert embedding1 != embedding2
        assert len(embedding1) == len(embedding2) == 1536 