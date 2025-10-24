"""
Pytest configuration and common fixtures for all tests
"""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import Mock, patch
from apps.core.models import CustomUser
from apps.directory.models import Contact
from apps.documents.models import Document
from apps.events.models import Event
from apps.donations.models import Donation, DonationType


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def user():
    """Test user"""
    return get_user_model().objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def admin_user():
    """Test admin user"""
    return get_user_model().objects.create_superuser(
        email='admin@example.com',
        username='admin',
        password='adminpass123'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Authenticated client with test user"""
    client.force_login(user)
    return client


@pytest.fixture
def contact():
    """Test contact"""
    return Contact.objects.create(
        first_name="Juan",
        last_name="Pérez",
        role="Pastor",
        ministry="Ministerio de Jóvenes",
        contact="juan@iglesia.com"
    )


@pytest.fixture
def document(user):
    """Test document"""
    return Document.objects.create(
        title="Test document",
        description="Test description",
        category="eventos_generales",
        user=user
    )


@pytest.fixture
def event():
    """Test event"""
    return Event.objects.create(
        title="Test event",
        description="Test event description",
        date="2024-12-25",
        time="18:00:00",
        location="Main Church"
    )


@pytest.fixture
def donation_type():
    """Test donation type"""
    return DonationType.objects.create(name="Monetary")


@pytest.fixture
def donation(user, donation_type):
    """Test donation"""
    return Donation.objects.create(
        title="Test donation",
        donation_type=donation_type,
        amount=100.00,
        description="Test donation description",
        method="deposito",
        entity="Bank of Mexico",
        created_by=user
    )


@pytest.fixture
def mock_cache():
    """Mock cache for testing"""
    with patch('django.core.cache.cache') as mock_cache:
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        yield mock_cache


@pytest.fixture
def whatsapp_context_data():
    """Sample WhatsApp context data for testing"""
    return {
        'session_id': 'test-session-123',
        'current_step': 'donation_info',
        'user_data': {
            'name': 'Juan Pérez',
            'phone': '+1234567890'
        },
        'conversation_history': [
            {'role': 'user', 'content': 'Hola'},
            {'role': 'assistant', 'content': '¿En qué puedo ayudarte?'}
        ]
    }


@pytest.fixture
def mock_acs_service():
    """Mock ACS service for testing"""
    mock_service = Mock()
    mock_service.send_template_message.return_value = {
        'success': True,
        'message_id': 'test-msg-123'
    }
    mock_service.send_text_message.return_value = {
        'success': True,
        'message_id': 'test-text-123'
    }
    return mock_service


@pytest.fixture
def mock_template_service():
    """Mock template service for testing"""
    mock_service = Mock()
    mock_service.detect_intent.return_value = ('donations', {})
    mock_service.get_template_for_intent.return_value = Mock()
    mock_service.prepare_template_parameters.return_value = {
        'customer_name': 'Juan Pérez',
        'bank_name': 'Banco Test'
    }
    return mock_service


@pytest.fixture
def mock_logging_service():
    """Mock logging service for testing"""
    mock_service = Mock()
    mock_service.log_interaction.return_value = Mock()
    mock_service.save_context_to_redis.return_value = True
    mock_service.get_context_from_redis.return_value = {}
    mock_service.update_context.return_value = True
    return mock_service


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test"""
    cache.clear()
    yield
    cache.clear() 