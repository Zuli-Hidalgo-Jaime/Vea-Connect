# VeaConnect Security Framework

## Overview

This document outlines the comprehensive security framework for the VeaConnect application, covering authentication, authorization, data protection, and compliance requirements for enterprise-grade security.

## Security Architecture

### Defense in Depth Strategy

The application implements a multi-layered security approach:

1. **Network Security**: VNet isolation, NSG rules, private endpoints
2. **Application Security**: Input validation, output encoding, secure coding practices
3. **Data Security**: Encryption at rest and in transit, access controls
4. **Identity Security**: Multi-factor authentication, role-based access control
5. **Monitoring Security**: Audit logging, threat detection, incident response

### Security Controls Matrix

| Control Category | Implementation | Compliance |
|------------------|----------------|------------|
| Access Control | Django RBAC, Azure AD integration | ISO 27001, SOC 2 |
| Data Protection | AES-256 encryption, TLS 1.3 | GDPR, CCPA |
| Network Security | VNet, NSG, private endpoints | NIST CSF |
| Application Security | Input validation, secure coding | OWASP Top 10 |
| Monitoring | Application Insights, Log Analytics | SOC 2, ISO 27001 |

## Authentication and Authorization

### User Authentication

```python
# config/settings/production.py
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'azure_ad_auth.backends.AzureADBackend',
]

# Azure AD Configuration
AZURE_AD = {
    'CLIENT_ID': os.environ.get('AZURE_AD_CLIENT_ID'),
    'CLIENT_SECRET': os.environ.get('AZURE_AD_CLIENT_SECRET'),
    'TENANT_ID': os.environ.get('AZURE_AD_TENANT_ID'),
    'RESOURCE': 'https://graph.microsoft.com',
}
```

### Role-Based Access Control

```python
# apps/core/models.py
class UserRole(models.Model):
    """User role definition for RBAC."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('pastor', 'Pastor'),
        ('deacon', 'Deacon'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permissions = models.ManyToManyField('Permission')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
```

### Permission Management

```python
# apps/core/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def role_required(allowed_roles):
    """Decorator to check user role permissions."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            user_role = getattr(request.user, 'role', None)
            if user_role not in allowed_roles:
                raise PermissionDenied("Insufficient permissions")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Usage example
@role_required(['admin', 'pastor'])
def sensitive_view(request):
    """View accessible only to administrators and pastors."""
    pass
```

## Data Protection

### Encryption Standards

#### Database Encryption

```python
# config/settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('AZURE_POSTGRESQL_NAME'),
        'USER': os.environ.get('AZURE_POSTGRESQL_USERNAME'),
        'PASSWORD': os.environ.get('AZURE_POSTGRESQL_PASSWORD'),
        'HOST': os.environ.get('AZURE_POSTGRESQL_HOST'),
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

#### File Storage Encryption

```python
# storage/backends.py
from storages.backends.azure_storage import AzureStorage
from cryptography.fernet import Fernet
import os

class EncryptedAzureStorage(AzureStorage):
    """Azure Storage with client-side encryption."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cipher = Fernet(os.environ.get('ENCRYPTION_KEY'))
    
    def _save(self, name, content):
        """Save file with encryption."""
        encrypted_content = self.cipher.encrypt(content.read())
        content.seek(0)
        content.write(encrypted_content)
        return super()._save(name, content)
    
    def _open(self, name, mode='rb'):
        """Open file with decryption."""
        file_obj = super()._open(name, mode)
        decrypted_content = self.cipher.decrypt(file_obj.read())
        return ContentFile(decrypted_content)
```

### Data Classification

```python
# apps/core/constants.py
class DataClassification:
    """Data classification levels."""
    
    PUBLIC = 'public'
    INTERNAL = 'internal'
    CONFIDENTIAL = 'confidential'
    RESTRICTED = 'restricted'

class DataTypes:
    """Data type definitions for classification."""
    
    PII = 'personally_identifiable_information'
    FINANCIAL = 'financial_data'
    HEALTH = 'health_information'
    RELIGIOUS = 'religious_preferences'
    CONTACT = 'contact_information'

# Usage in models
class Contact(models.Model):
    """Contact information with data classification."""
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Data classification
    data_classification = models.CharField(
        max_length=20,
        choices=[(c, c.title()) for c in DataClassification.__dict__.keys() 
                if not c.startswith('_')],
        default=DataClassification.CONFIDENTIAL
    )
    
    class Meta:
        permissions = [
            ("view_confidential_contacts", "Can view confidential contact data"),
            ("export_contact_data", "Can export contact data"),
        ]
```

## Input Validation and Sanitization

### Form Validation

```python
# apps/core/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

def validate_safe_text(value):
    """Validate text input for XSS prevention."""
    if not value:
        return value
    
    # Remove HTML tags
    cleaned_value = strip_tags(value)
    
    # Check for script injection
    script_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'vbscript:',
    ]
    
    for pattern in script_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError("Potentially unsafe content detected")
    
    return cleaned_value

def validate_file_type(uploaded_file):
    """Validate uploaded file type."""
    allowed_types = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
    
    if uploaded_file.content_type not in allowed_types:
        raise ValidationError("File type not allowed")
    
    # Check file size (10MB limit)
    if uploaded_file.size > 10 * 1024 * 1024:
        raise ValidationError("File size exceeds 10MB limit")

# Usage in forms
class SecureContactForm(forms.ModelForm):
    """Contact form with security validation."""
    
    first_name = forms.CharField(
        max_length=100,
        validators=[validate_safe_text]
    )
    last_name = forms.CharField(
        max_length=100,
        validators=[validate_safe_text]
    )
    email = forms.EmailField()
    
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'email', 'phone']
    
    def clean(self):
        """Additional form-level validation."""
        cleaned_data = super().clean()
        
        # Validate email domain
        email = cleaned_data.get('email')
        if email:
            domain = email.split('@')[1]
            if domain in ['disposable.com', 'temp-mail.org']:
                raise ValidationError("Disposable email addresses not allowed")
        
        return cleaned_data
```

### API Security

```python
# apps/core/api_security.py
from rest_framework import permissions
from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache

class SecureAPIViewMixin:
    """Mixin for secure API views."""
    
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Apply row-level security
        if hasattr(self.request.user, 'role'):
            if self.request.user.role.role == 'member':
                # Members can only see their own data
                queryset = queryset.filter(created_by=self.request.user)
            elif self.request.user.role.role == 'deacon':
                # Deacons can see ministry-related data
                queryset = queryset.filter(ministry=self.request.user.ministry)
        
        return queryset

class AuditLogMixin:
    """Mixin for audit logging."""
    
    def perform_create(self, serializer):
        """Log creation events."""
        instance = serializer.save(created_by=self.request.user)
        
        # Log audit event
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            model_name=instance.__class__.__name__,
            object_id=instance.id,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
        )
        
        return instance
```

## Network Security

### Azure Network Configuration

```bash
# Network Security Group Rules
az network nsg rule create \
  --name allow-https \
  --nsg-name vea-connect-nsg \
  --resource-group vea-connect-rg \
  --protocol tcp \
  --priority 100 \
  --destination-port-range 443 \
  --access allow \
  --description "Allow HTTPS traffic"

az network nsg rule create \
  --name deny-all \
  --nsg-name vea-connect-nsg \
  --resource-group vea-connect-rg \
  --protocol * \
  --priority 4096 \
  --destination-port-range * \
  --access deny \
  --description "Deny all other traffic"
```

### Private Endpoints

```bash
# Configure private endpoints for secure communication
az network private-endpoint create \
  --name postgres-private-endpoint \
  --resource-group vea-connect-rg \
  --vnet-name vea-connect-vnet \
  --subnet default \
  --private-connection-resource-id <postgres_resource_id> \
  --group-id postgresqlServer \
  --connection-name postgres-connection
```

## Monitoring and Logging

### Security Event Logging

```python
# apps/core/logging.py
import logging
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

class SecurityLogger:
    """Centralized security logging."""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_authentication_event(self, user, event_type, success, details=None):
        """Log authentication events."""
        log_data = {
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'event_type': event_type,
            'success': success,
            'ip_address': self.get_client_ip(),
            'user_agent': self.get_user_agent(),
            'details': details or {},
        }
        
        self.logger.info(f"Authentication event: {log_data}")
        
        # Store in database for compliance
        SecurityEvent.objects.create(**log_data)
    
    def log_data_access(self, user, model_name, object_id, action):
        """Log data access events."""
        log_data = {
            'user': user,
            'model_name': model_name,
            'object_id': object_id,
            'action': action,
            'timestamp': timezone.now(),
        }
        
        self.logger.info(f"Data access: {log_data}")
        
        # Create admin log entry
        content_type = ContentType.objects.get(model=model_name.lower())
        LogEntry.objects.create(
            user_id=user.id,
            content_type_id=content_type.id,
            object_id=object_id,
            object_repr=f"{model_name}:{object_id}",
            action_flag=action,
            change_message=f"Data access logged for {action}",
        )

# Usage
security_logger = SecurityLogger()

def login_view(request):
    """Secure login view with logging."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            security_logger.log_authentication_event(
                user, 'login', True, {'method': 'password'}
            )
            return redirect('dashboard')
        else:
            security_logger.log_authentication_event(
                None, 'login', False, {'username': username}
            )
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'login.html')
```

### Threat Detection

```python
# apps/core/security_monitoring.py
from django.core.cache import cache
from django.http import HttpResponseForbidden
import time

class ThreatDetectionMiddleware:
    """Middleware for threat detection and prevention."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Rate limiting
        if self.is_rate_limited(request):
            return HttpResponseForbidden("Rate limit exceeded")
        
        # Suspicious activity detection
        if self.detect_suspicious_activity(request):
            self.log_security_event(request, 'suspicious_activity')
            return HttpResponseForbidden("Suspicious activity detected")
        
        response = self.get_response(request)
        return response
    
    def is_rate_limited(self, request):
        """Check if request exceeds rate limits."""
        client_ip = self.get_client_ip(request)
        cache_key = f"rate_limit:{client_ip}"
        
        request_count = cache.get(cache_key, 0)
        if request_count > 100:  # 100 requests per minute
            return True
        
        cache.set(cache_key, request_count + 1, 60)
        return False
    
    def detect_suspicious_activity(self, request):
        """Detect suspicious patterns in requests."""
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'../',
            r'\.\./',
            r'UNION.*SELECT',
            r'DROP.*TABLE',
        ]
        
        request_path = request.path
        request_data = str(request.POST) + str(request.GET)
        
        for pattern in suspicious_patterns:
            if re.search(pattern, request_path + request_data, re.IGNORECASE):
                return True
        
        return False
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

## Compliance and Governance

### GDPR Compliance

```python
# apps/core/gdpr.py
from django.db import models
from django.contrib.auth.models import User

class DataSubject(models.Model):
    """Data subject information for GDPR compliance."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    data_retention_period = models.IntegerField(default=365)  # days
    right_to_erasure = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Data Subject'
        verbose_name_plural = 'Data Subjects'

class DataProcessingActivity(models.Model):
    """Data processing activities for GDPR compliance."""
    
    name = models.CharField(max_length=200)
    purpose = models.TextField()
    legal_basis = models.CharField(max_length=100)
    data_categories = models.JSONField()
    retention_period = models.IntegerField()  # days
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Data Processing Activity'
        verbose_name_plural = 'Data Processing Activities'

def handle_data_subject_request(user, request_type):
    """Handle GDPR data subject requests."""
    
    if request_type == 'access':
        return generate_data_export(user)
    elif request_type == 'erasure':
        return anonymize_user_data(user)
    elif request_type == 'portability':
        return export_user_data(user)
    elif request_type == 'rectification':
        return allow_data_rectification(user)

def generate_data_export(user):
    """Generate data export for GDPR access requests."""
    from django.core import serializers
    import json
    
    user_data = {
        'profile': serializers.serialize('json', [user]),
        'contacts': serializers.serialize('json', user.contact_set.all()),
        'donations': serializers.serialize('json', user.donation_set.all()),
        'events': serializers.serialize('json', user.event_set.all()),
    }
    
    return json.dumps(user_data, indent=2)
```

### Security Policy Enforcement

```python
# apps/core/security_policies.py
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class SecurityPolicy:
    """Security policy enforcement."""
    
    @staticmethod
    def enforce_password_policy(password):
        """Enforce strong password policy."""
        if len(password) < 12:
            raise ValidationError("Password must be at least 12 characters long")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character")
    
    @staticmethod
    def enforce_session_policy(request):
        """Enforce session security policy."""
        if request.user.is_authenticated:
            # Check session age
            session_age = timezone.now() - request.session.get('last_activity', timezone.now())
            if session_age > timedelta(hours=8):
                return False  # Session expired
            
            # Update last activity
            request.session['last_activity'] = timezone.now().isoformat()
        
        return True
    
    @staticmethod
    def enforce_mfa_policy(user):
        """Enforce multi-factor authentication policy."""
        if user.role.role in ['admin', 'pastor']:
            if not hasattr(user, 'mfa_device') or not user.mfa_device.is_active:
                return False
        
        return True
```

## Incident Response

### Security Incident Procedures

```python
# apps/core/incident_response.py
from django.core.mail import send_mail
from django.conf import settings
import logging

class SecurityIncidentHandler:
    """Handle security incidents."""
    
    def __init__(self):
        self.logger = logging.getLogger('security_incident')
    
    def handle_incident(self, incident_type, details, severity='medium'):
        """Handle security incident."""
        
        # Log incident
        self.logger.critical(f"Security incident: {incident_type} - {details}")
        
        # Create incident record
        incident = SecurityIncident.objects.create(
            incident_type=incident_type,
            details=details,
            severity=severity,
            status='open',
            created_at=timezone.now(),
        )
        
        # Notify security team
        self.notify_security_team(incident)
        
        # Take immediate action based on severity
        if severity == 'high':
            self.take_emergency_action(incident)
        elif severity == 'medium':
            self.take_standard_action(incident)
        else:
            self.monitor_incident(incident)
        
        return incident
    
    def notify_security_team(self, incident):
        """Notify security team of incident."""
        subject = f"Security Incident: {incident.incident_type}"
        message = f"""
        Security incident detected:
        
        Type: {incident.incident_type}
        Severity: {incident.severity}
        Details: {incident.details}
        Time: {incident.created_at}
        
        Please review and take appropriate action.
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.SECURITY_EMAIL,
            recipient_list=settings.SECURITY_TEAM_EMAILS,
            fail_silently=False,
        )
    
    def take_emergency_action(self, incident):
        """Take emergency action for high-severity incidents."""
        # Block suspicious IP addresses
        if 'ip_address' in incident.details:
            self.block_ip_address(incident.details['ip_address'])
        
        # Disable compromised accounts
        if 'user_id' in incident.details:
            self.disable_user_account(incident.details['user_id'])
        
        # Trigger incident response procedures
        self.trigger_incident_response(incident)
```

---

**Document Version**: 2.0  
**Last Updated**: December 2024  
**Next Review**: March 2025  
**Classification**: Internal Use Only - Security Sensitive 