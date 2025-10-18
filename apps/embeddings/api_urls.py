from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .api_views import (
    EmbeddingViewSet,
    SearchViewSet,
    HealthCheckView,
    StatisticsView,
    SearchLogViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'embeddings', EmbeddingViewSet, basename='embedding')
router.register(r'search', SearchViewSet, basename='search')
router.register(r'search-logs', SearchLogViewSet, basename='search-log')

# URL patterns for API endpoints
urlpatterns = [
    # JWT Authentication endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Health check and statistics
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    
    # Include router URLs
    path('', include(router.urls)),
] 