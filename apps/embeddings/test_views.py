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