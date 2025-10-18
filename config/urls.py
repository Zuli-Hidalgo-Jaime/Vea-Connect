"""
Main URL configuration for the project.

This module defines the URL patterns for the entire application,
including API endpoints, admin interface, and static files.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
import apps.embeddings.views
from apps.core import views as core_views

# Swagger/OpenAPI schema view
schema_view = get_schema_view(
    openapi.Info(
        title="VEA WebApp API",
        default_version='v1',
        description="API documentation for VEA WebApp",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@vea.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Core app URLs
    path('', include('apps.core.urls')),
    
    # Dashboard URLs
    path('dashboard/', include('apps.dashboard.urls')),
    
    # App-specific URLs
    path('donations/', include('apps.donations.urls')),
    path('directory/', include('apps.directory.urls')),
    path('documents/', include('apps.documents.urls')),
    path('events/', include('apps.events.urls')),
    path('embeddings/', include('apps.embeddings.urls')),
    path('vision/', include('apps.vision.urls')),
    path('user-settings/', include('apps.user_settings.urls')),
    
    # API URLs
    path('api/v1/', include('apps.embeddings.api_urls')),
    path('api/v1/whatsapp/', include('apps.whatsapp_bot.urls')),
    
    # Simple health check
    path('health/', lambda r: HttpResponse("OK")),
    
    # Operations endpoints (admin only)
    path('ops/cache/stats/', core_views.cache_stats_view, name='cache_stats'),
    
    # Additional URL patterns for tests
    path('home/', core_views.index_view, name='home'),
    path('contact/create/', apps.directory.views.contact_create, name='contact_create'),
    path('contact/delete/<int:pk>/', apps.directory.views.contact_delete, name='contact_delete'),
    path('document/create/', apps.documents.views.upload_document, name='document_create'),
    path('document/delete/<int:pk>/', apps.documents.views.delete_document, name='document_delete'),
    path('event/create/', apps.events.views.event_create, name='event_create'),
    path('event/delete/<int:pk>/', apps.events.views.event_delete, name='event_delete'),
    
    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API schema
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
