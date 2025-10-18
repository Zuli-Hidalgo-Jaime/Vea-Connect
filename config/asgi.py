"""
ASGI config for veaconnect project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar el módulo de settings por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')

from django.core.asgi import get_asgi_application
application = get_asgi_application()
