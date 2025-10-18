from django.urls import path
from .test_views import TestHealthView
 
# Simple URL patterns for testing
urlpatterns = [
    # Health check and statistics
    path('health/', TestHealthView.as_view(), name='health_check'),
] 