# VeaConnect Testing Framework

## Overview

This document outlines the comprehensive testing strategy for the VeaConnect application, covering unit tests, integration tests, security tests, and performance validation using Pytest and Django TestCase.

## Testing Architecture

### Test Categories

- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: End-to-end workflow validation
- **Security Tests**: Authentication, authorization, and vulnerability testing
- **Performance Tests**: Load testing and performance validation
- **API Tests**: REST API endpoint validation

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_forms.py       # Form validation tests
│   ├── test_models.py      # Model behavior tests
│   ├── test_views.py       # View logic tests
│   └── test_services.py    # Business logic tests
├── integration/            # Integration tests
│   ├── test_api.py         # API integration tests
│   ├── test_workflows.py   # End-to-end workflow tests
│   └── test_database.py    # Database integration tests
├── security/               # Security-specific tests
│   ├── test_authentication.py
│   ├── test_authorization.py
│   └── test_vulnerabilities.py
├── performance/            # Performance tests
│   ├── test_load.py        # Load testing
│   └── test_stress.py      # Stress testing
└── conftest.py            # Pytest configuration and fixtures
```

## Testing Standards

### Code Quality Requirements

- **Test Coverage**: Minimum 80% code coverage
- **Type Safety**: Pyright compliance for all test code
- **Documentation**: Comprehensive test documentation
- **Maintainability**: Clean, readable test code

### Test Naming Conventions

```python
# Test class naming
class TestUserAuthentication(TestCase):
    """Tests for user authentication functionality."""
    
    def test_user_login_with_valid_credentials(self):
        """Test successful user login with valid credentials."""
        pass
    
    def test_user_login_with_invalid_credentials(self):
        """Test failed user login with invalid credentials."""
        pass
```

### Test Data Management

```python
# Fixture-based test data
@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(client, sample_user):
    """Create an authenticated client for testing."""
    client.force_login(sample_user)
    return client
```

## Unit Testing Framework

### Form Testing

```python
from django.test import TestCase
from django.forms.utils import ErrorDict
from typing import cast
from apps.directory.forms import ContactForm

class ContactFormTest(TestCase):
    """Tests for ContactForm validation and behavior."""
    
    def test_contact_form_valid_data(self):
        """Test form validation with valid data."""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'Pastor',
            'ministry': 'Youth Ministry',
            'contact': 'john.doe@church.com'
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_contact_form_invalid_data(self):
        """Test form validation with invalid data."""
        form = ContactForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('ministry', errors)
        self.assertIn('contact', errors)
```

### Model Testing

```python
from django.test import TestCase
from apps.directory.models import Contact

class ContactModelTest(TestCase):
    """Tests for Contact model behavior."""
    
    def test_contact_creation(self):
        """Test contact object creation."""
        contact = Contact.objects.create(
            first_name='Jane',
            last_name='Smith',
            role='Deacon',
            ministry='Outreach',
            contact='jane.smith@church.com'
        )
        self.assertEqual(contact.full_name, 'Jane Smith')
        self.assertEqual(contact.role, 'Deacon')
    
    def test_contact_str_representation(self):
        """Test string representation of contact."""
        contact = Contact.objects.create(
            first_name='Bob',
            last_name='Johnson',
            role='Elder'
        )
        self.assertEqual(str(contact), 'Bob Johnson - Elder')
```

### View Testing

```python
from django.test import TestCase, Client
from django.urls import reverse
from apps.directory.models import Contact

class ContactViewTest(TestCase):
    """Tests for contact-related views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.contact = Contact.objects.create(
            first_name='Test',
            last_name='User',
            role='Member'
        )
    
    def test_contact_list_view(self):
        """Test contact list view."""
        response = self.client.get(reverse('contact_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
    
    def test_contact_detail_view(self):
        """Test contact detail view."""
        response = self.client.get(
            reverse('contact_detail', args=[self.contact.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.contact.first_name)
```

## Integration Testing

### API Testing

```python
from rest_framework.test import APITestCase
from rest_framework import status
from apps.directory.models import Contact

class ContactAPITest(APITestCase):
    """Tests for contact API endpoints."""
    
    def test_contact_list_api(self):
        """Test contact list API endpoint."""
        Contact.objects.create(
            first_name='API',
            last_name='Test',
            role='Member'
        )
        
        response = self.client.get('/api/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_contact_create_api(self):
        """Test contact creation API endpoint."""
        data = {
            'first_name': 'New',
            'last_name': 'Contact',
            'role': 'Member',
            'ministry': 'Youth',
            'contact': 'new.contact@church.com'
        }
        
        response = self.client.post('/api/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 1)
```

### Database Integration Testing

```python
from django.test import TestCase, TransactionTestCase
from apps.donations.models import Donation, DonationType

class DonationIntegrationTest(TransactionTestCase):
    """Tests for donation database integration."""
    
    def test_donation_creation_with_type(self):
        """Test donation creation with donation type."""
        donation_type = DonationType.objects.create(name='Monetary')
        donation = Donation.objects.create(
            title='Test Donation',
            donation_type=donation_type,
            amount=100.00
        )
        
        self.assertEqual(donation.donation_type.name, 'Monetary')
        self.assertEqual(donation.amount, 100.00)
    
    def test_donation_cascade_deletion(self):
        """Test cascade deletion behavior."""
        donation_type = DonationType.objects.create(name='Food')
        donation = Donation.objects.create(
            title='Food Donation',
            donation_type=donation_type
        )
        
        donation_type.delete()
        self.assertEqual(Donation.objects.count(), 0)
```

## Security Testing

### Authentication Testing

```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

class AuthenticationTest(TestCase):
    """Tests for authentication functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
    
    def test_login_success(self):
        """Test successful user login."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'securepass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_failure(self):
        """Test failed user login."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_logout(self):
        """Test user logout."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
```

### Authorization Testing

```python
from django.test import TestCase, Client
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class AuthorizationTest(TestCase):
    """Tests for authorization and permissions."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
        self.admin_user = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
    
    def test_unauthorized_access(self):
        """Test unauthorized access to protected views."""
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)
    
    def test_authorized_access(self):
        """Test authorized access to protected views."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
    
    def test_permission_based_access(self):
        """Test permission-based access control."""
        content_type = ContentType.objects.get_for_model(Contact)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_contact'
        )
        self.user.user_permissions.add(permission)
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('contact_create'))
        self.assertEqual(response.status_code, 200)
```

## Performance Testing

### Load Testing

```python
import time
from django.test import TestCase, Client
from django.urls import reverse

class PerformanceTest(TestCase):
    """Tests for application performance."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        # Create test data for performance testing
    
    def test_homepage_load_time(self):
        """Test homepage load time under normal conditions."""
        start_time = time.time()
        response = self.client.get(reverse('home'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Should load in under 1 second
    
    def test_database_query_performance(self):
        """Test database query performance."""
        # Create multiple test records
        for i in range(100):
            Contact.objects.create(
                first_name=f'User{i}',
                last_name=f'Test{i}',
                role='Member'
            )
        
        start_time = time.time()
        contacts = Contact.objects.all()
        end_time = time.time()
        
        self.assertEqual(contacts.count(), 100)
        self.assertLess(end_time - start_time, 0.1)  # Should query in under 0.1 seconds
```

## Test Configuration

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    security: Security tests
    performance: Performance tests
    slow: Slow running tests
```

### Test Settings

```python
# config/settings/test.py
from .base import *

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

# Use in-memory database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Test-specific settings
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```

## Test Execution

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m security
pytest -m performance

# Run tests with coverage
pytest --cov=apps --cov-report=html

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tests/unit/test_forms.py

# Run specific test function
pytest tests/unit/test_forms.py::ContactFormTest::test_contact_form_valid_data
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      run: |
        pytest --cov=apps --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Test Maintenance

### Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Test Data**: Use factories or fixtures for test data creation
3. **Mocking**: Mock external dependencies to ensure test reliability
4. **Assertions**: Use specific assertions that clearly indicate test intent
5. **Documentation**: Document complex test scenarios and business logic

### Test Review Process

1. **Code Review**: All test code must be reviewed by peers
2. **Coverage Analysis**: Regular review of test coverage metrics
3. **Performance Monitoring**: Track test execution time and optimize slow tests
4. **Maintenance Schedule**: Regular review and cleanup of outdated tests

---

**Document Version**: 2.0  
**Last Updated**: December 2024  
**Next Review**: March 2025  
**Classification**: Internal Use Only 