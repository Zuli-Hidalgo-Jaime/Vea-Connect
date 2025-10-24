#!/usr/bin/env python3
"""
Prueba rápida de embeddings.
"""

import requests
import json

BASE_URL = "http://localhost:7075/api"

def test_embeddings_create_simple():
    """Prueba simple de creación de embeddings."""
    print("🧪 Prueba Rápida de Embeddings")
    print("=" * 40)
    
    url = f"{BASE_URL}/embeddings/create"
    
    test_data = {
        "text": "Texto de prueba simple",
        "metadata": {
            "test": True,
            "source": "quick_test"
        }
    }
    
    try:
        print(f"Enviando request a: {url}")
        
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ ¡Éxito! Embedding creado correctamente")
            return True
        else:
            print("❌ Error en la creación")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_embeddings_create_simple() 
