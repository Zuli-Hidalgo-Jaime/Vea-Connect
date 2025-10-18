from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

def index_view(request):
    """Vista principal de la aplicación."""
    return render(request, 'core/index.html')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Inicia sesión automáticamente tras registrar
            return redirect('dashboard:home')  # Redirige al dashboard
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

@staff_member_required
@require_http_methods(["GET"])
def cache_stats_view(request):
    """
    Endpoint para obtener estadísticas del cache Redis.
    Solo accesible para administradores.
    """
    try:
        # Import cache layer
        from utils.cache_layer import get_cache_stats, is_cache_enabled
        
        if not is_cache_enabled():
            return JsonResponse({
                'enabled': False,
                'reason': 'Cache layer disabled'
            }, status=200)
        
        stats = get_cache_stats()
        logger.info(f"Cache stats requested by admin: {request.user.username}")
        
        return JsonResponse(stats, status=200)
        
    except ImportError:
        logger.warning("Cache layer not available")
        return JsonResponse({
            'enabled': False,
            'reason': 'Cache layer not available'
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)
