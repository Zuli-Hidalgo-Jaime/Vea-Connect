# Code Standards and Best Practices

This document outlines the coding standards and best practices for the VEA Connect WebApp project.

## Table of Contents

1. [Python Standards](#python-standards)
2. [Django Standards](#django-standards)
3. [Security Guidelines](#security-guidelines)
4. [Testing Standards](#testing-standards)
5. [Documentation Standards](#documentation-standards)
6. [Git Workflow](#git-workflow)

## Python Standards

### Code Style

- **Formatter**: Use Black with line length of 119 characters
- **Linter**: Use Flake8 with project-specific configuration
- **Type Checking**: Use Pyright for static type checking
- **Import Sorting**: Use isort with Black profile

### Naming Conventions

```python
# Variables and functions: snake_case
user_name = "john_doe"
def calculate_total_amount():
    pass

# Classes: PascalCase
class UserProfile:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# Private methods: leading underscore
def _internal_helper():
    pass
```

### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import List, Dict, Optional, Any

def process_user_data(user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process user data and return result."""
    pass

def get_user_list(active_only: bool = True) -> List[Dict[str, Any]]:
    """Get list of users."""
    pass
```

### Error Handling

Use specific exception handling:

```python
try:
    result = some_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    # Handle gracefully
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## Django Standards

### Model Definitions

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    """User profile model with comprehensive documentation."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.email} Profile"

    def get_full_name(self) -> str:
        """Return user's full name."""
        return f"{self.user.first_name} {self.user.last_name}".strip()
```

### View Patterns

Use class-based views when possible:

```python
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

class DonationListView(LoginRequiredMixin, ListView):
    """Display list of donations."""
    
    model = Donation
    template_name = 'donations/donation_list.html'
    context_object_name = 'donations'
    paginate_by = 20

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['total_amount'] = self.get_queryset().aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        return context
```

### Form Validation

```python
from django import forms
from django.core.exceptions import ValidationError

class DonationForm(forms.ModelForm):
    """Form for creating and editing donations."""
    
    class Meta:
        model = Donation
        fields = ['title', 'description', 'amount', 'donation_type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_amount(self):
        """Validate donation amount."""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('Amount must be greater than zero.')
        return amount

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        description = cleaned_data.get('description')
        
        if title and description and title.lower() in description.lower():
            raise ValidationError('Description should not contain the title.')
        
        return cleaned_data
```

## Security Guidelines

### Input Validation

Always validate and sanitize user input:

```python
import re
from django.core.exceptions import ValidationError

def validate_phone_number(phone_number: str) -> str:
    """Validate and format phone number."""
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone_number)
    
    if len(cleaned) < 10:
        raise ValidationError('Phone number must have at least 10 digits.')
    
    return f"+1{cleaned}"  # Format for US numbers
```

### SQL Injection Prevention

Use Django ORM or parameterized queries:

```python
# Good: Use Django ORM
users = User.objects.filter(email__icontains=search_term)

# Good: Use parameterized queries
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM users WHERE email LIKE %s",
        [f'%{search_term}%']
    )

# Bad: String concatenation (vulnerable to SQL injection)
cursor.execute(f"SELECT * FROM users WHERE email LIKE '%{search_term}%'")
```

### XSS Prevention

Use Django's template escaping:

```html
<!-- Good: Django automatically escapes -->
<p>{{ user_input }}</p>

<!-- Good: Explicit escaping -->
<p>{{ user_input|escape }}</p>

<!-- Bad: Mark as safe without validation -->
<p>{{ user_input|safe }}</p>
```

### CSRF Protection

Always include CSRF tokens in forms:

```html
<form method="post">
    {% csrf_token %}
    {{ form }}
    <button type="submit">Submit</button>
</form>
```

## Testing Standards

### Test Structure

```python
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class DonationModelTest(TestCase):
    """Test cases for Donation model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.donation = Donation.objects.create(
            title='Test Donation',
            amount=100.00,
            created_by=self.user
        )

    def test_donation_creation(self):
        """Test donation creation."""
        self.assertEqual(self.donation.title, 'Test Donation')
        self.assertEqual(self.donation.amount, 100.00)
        self.assertEqual(self.donation.created_by, self.user)

    def test_donation_str_representation(self):
        """Test string representation."""
        expected = f"Test Donation - $100.00"
        self.assertEqual(str(self.donation), expected)

    def test_donation_amount_validation(self):
        """Test amount validation."""
        with self.assertRaises(ValidationError):
            Donation.objects.create(
                title='Invalid Donation',
                amount=-50.00,
                created_by=self.user
            )
```

### API Testing

```python
from rest_framework.test import APITestCase
from rest_framework import status

class DonationAPITest(APITestCase):
    """Test cases for donation API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_donation(self):
        """Test donation creation via API."""
        url = reverse('api:donation-create')
        data = {
            'title': 'API Test Donation',
            'amount': 150.00,
            'donation_type': 'monetary'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Donation.objects.count(), 1)
        
        donation = Donation.objects.first()
        self.assertEqual(donation.title, 'API Test Donation')
        self.assertEqual(donation.amount, 150.00)
```

## Documentation Standards

### Docstrings

Use Google-style docstrings:

```python
def process_donation(donation_id: int, amount: float) -> Dict[str, Any]:
    """Process a donation and update related records.
    
    Args:
        donation_id: The ID of the donation to process
        amount: The amount to process
        
    Returns:
        Dictionary containing processing results
        
    Raises:
        DonationNotFoundError: If donation doesn't exist
        InvalidAmountError: If amount is invalid
        
    Example:
        >>> result = process_donation(123, 100.00)
        >>> print(result['status'])
        'success'
    """
    pass
```

### Comments

Write meaningful comments:

```python
# Calculate total donations for the current month
current_month_donations = Donation.objects.filter(
    created_at__month=timezone.now().month,
    created_at__year=timezone.now().year
).aggregate(total=models.Sum('amount'))['total'] or 0

# Apply 10% discount for donations over $1000
if current_month_donations > 1000:
    discount_amount = current_month_donations * 0.10
    final_amount = current_month_donations - discount_amount
else:
    final_amount = current_month_donations
```

## Git Workflow

### Branch Naming

- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes
- `refactor/component-name` - Code refactoring

### Commit Messages

Use conventional commit format:

```
feat: add donation processing functionality
fix: resolve SQL injection vulnerability in user search
docs: update API documentation
refactor: simplify donation validation logic
test: add comprehensive test coverage for donation API
```

### Pull Request Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: Detailed description of changes
3. **Testing**: Include test results and coverage
4. **Review**: Request reviews from appropriate team members
5. **CI/CD**: Ensure all checks pass before merging

## Code Review Checklist

### Security
- [ ] Input validation implemented
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Authentication/authorization checks

### Quality
- [ ] Code follows style guidelines
- [ ] Type hints included
- [ ] Error handling implemented
- [ ] Logging appropriate
- [ ] Documentation updated

### Testing
- [ ] Unit tests written
- [ ] Integration tests included
- [ ] Test coverage adequate
- [ ] Edge cases covered

### Performance
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Appropriate caching implemented
- [ ] Memory usage considered

## Tools and Automation

### Pre-commit Hooks

The project uses pre-commit hooks to enforce standards:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: [--line-length=119]
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--config=.flake8]
```

### CI/CD Integration

Automated checks run on every pull request:

- Code formatting (Black)
- Linting (Flake8)
- Type checking (Pyright)
- Security scanning (Bandit)
- Test execution (Pytest)
- Coverage reporting

## Performance Guidelines

### Database Optimization

```python
# Good: Use select_related for foreign keys
donations = Donation.objects.select_related('created_by').all()

# Good: Use prefetch_related for many-to-many
events = Event.objects.prefetch_related('participants').all()

# Good: Use only() to limit fields
users = User.objects.only('id', 'email', 'first_name').all()
```

### Caching

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def expensive_view(request):
    """Expensive operation with caching."""
    pass

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get user data with caching."""
    cache_key = f"user_data_{user_id}"
    user_data = cache.get(cache_key)
    
    if user_data is None:
        user_data = expensive_database_query(user_id)
        cache.set(cache_key, user_data, timeout=3600)  # 1 hour
    
    return user_data
```

## Monitoring and Logging

### Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

def process_payment(payment_data: Dict[str, Any]) -> bool:
    """Process payment with comprehensive logging."""
    logger.info(f"Processing payment for user {payment_data['user_id']}")
    
    try:
        result = payment_processor.charge(payment_data)
        logger.info(f"Payment successful: {result['transaction_id']}")
        return True
    except PaymentError as e:
        logger.error(f"Payment failed: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error in payment processing: {e}")
        return False
```

### Performance Monitoring

```python
from django.core.cache import cache
import time

def monitored_function():
    """Function with performance monitoring."""
    start_time = time.time()
    
    try:
        result = expensive_operation()
        
        # Log performance metrics
        execution_time = time.time() - start_time
        cache.incr(f"function_execution_time_{__name__}", execution_time)
        
        return result
    except Exception as e:
        logger.exception(f"Error in {__name__}: {e}")
        raise
```

---

**Last Updated**: December 2024  
**Next Review**: March 2025  
**Maintained By**: Development Team
