#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run administrative tasks."""

    # Selecciona settings en función del entorno
    settings_module = "config.settings.azure_production" if 'WEBSITE_HOSTNAME' in os.environ else 'config.settings.development'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    # Carga .env solo en desarrollo local y si está disponible
    if 'WEBSITE_HOSTNAME' not in os.environ:
        try:
            from dotenv import load_dotenv
            print("Cargando variables desde .env (modo local)")
            load_dotenv('./.env')
        except ImportError:
            print("python-dotenv no está instalado, continuando sin .env")
        except Exception as e:
            print(f"Error cargando .env: {e}, continuando sin .env")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Activaste tu entorno virtual?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
