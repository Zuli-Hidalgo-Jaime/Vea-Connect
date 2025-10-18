from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Simple test view
from django.http import JsonResponse
from django.views import View

class TestHealthView(View):
    """Simple test view for health check."""
    
    def get(self, request):
        """Return a simple health check response."""
        return JsonResponse({
            'status': 'healthy',
            'message': 'API is working!',
            'timestamp': '2024-01-15T10:30:00Z'
        })

# URL patterns for API endpoints (simplified)
urlpatterns = [
    # JWT Authentication endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Health check (simplified)
    path('health/', TestHealthView.as_view(), name='health_check'),
] 