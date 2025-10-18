from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Swagger/OpenAPI schema view
schema_view = get_schema_view(
    openapi.Info(
        title="VEA Connect API",
        default_version='v1',
        description="API for VEA Connect application with embeddings and semantic search",
        terms_of_service="https://www.veaconnect.com/terms/",
        contact=openapi.Contact(email="contact@veaconnect.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Debug function to test API URL import
def debug_api_urls():
    """Debug function to test API URL import."""
    try:
        logger.info("Attempting to import API URLs...")
        from apps.embeddings.api_urls import urlpatterns
        logger.info(f"✅ API URLs imported successfully: {len(urlpatterns)} patterns")
        return True
    except Exception as e:
        logger.error(f"❌ Error importing API URLs: {e}")
        return False

# Test the import
debug_api_urls()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('documents/', include('apps.documents.urls')),
    path('events/', include('apps.events.urls')),
    path('directory/', include('apps.directory.urls')),
    path('donations/', include('apps.donations.urls')),
    path('user-settings/', include('apps.user_settings.urls')),
    path('embeddings/', include('apps.embeddings.urls')),
    path('vision/', include('apps.vision.urls')),
    
    # API endpoints with explicit import
    path('api/v1/', include('apps.embeddings.api_urls')),
    
    # Swagger/OpenAPI documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Log URL patterns for debugging
logger.info(f"Total URL patterns loaded: {len(urlpatterns)}")
for i, pattern in enumerate(urlpatterns):
    logger.info(f"  {i+1}. {pattern.pattern}") 