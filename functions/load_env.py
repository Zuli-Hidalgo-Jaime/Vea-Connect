#!/usr/bin/env python3
"""
Cargar variables de entorno desde local.settings.json
"""

import json
import os
import sys

def load_local_settings():
    """Cargar variables desde local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        # Cargar variables de entorno
        for key, value in settings.get('Values', {}).items():
            os.environ[key] = value
        
        print(f"✅ Cargadas {len(settings.get('Values', {}))} variables de entorno")
        return True
        
    except FileNotFoundError:
        print("❌ No se encontró local.settings.json")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error cargando variables: {e}")
        return False

if __name__ == "__main__":
    load_local_settings()
