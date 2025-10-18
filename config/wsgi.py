"""
WSGI config for veaconnect project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Agregar el directorio del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configurar el módulo de settings por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
