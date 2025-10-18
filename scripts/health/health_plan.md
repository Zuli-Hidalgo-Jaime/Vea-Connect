# Health Plan - VEA Connect Platform

## Objetivo
Plan detallado para verificar la salud de todas las dependencias de la plataforma sin crear endpoints nuevos.

## 1. Azure Storage Health Check

### Comandos de Verificación

#### 1.1 Verificar Configuración
```bash
# Verificar variables de entorno
echo $AZURE_STORAGE_CONNECTION_STRING
echo $AZURE_STORAGE_ACCOUNT_NAME
echo $AZURE_STORAGE_CONTAINER_NAME

# Verificar desde Python
python -c "
import os
print('AZURE_STORAGE_CONNECTION_STRING:', 'SET' if os.getenv('AZURE_STORAGE_CONNECTION_STRING') else 'NOT SET')
print('AZURE_STORAGE_ACCOUNT_NAME:', 'SET' if os.getenv('AZURE_STORAGE_ACCOUNT_NAME') else 'NOT SET')
print('AZURE_STORAGE_CONTAINER_NAME:', 'SET' if os.getenv('AZURE_STORAGE_CONTAINER_NAME') else 'NOT SET')
"
```

#### 1.2 Verificar Conexión
```python
# Script de verificación
from services.storage_service import azure_storage
import time

start_time = time.time()
result = azure_storage.list_blobs()
latency = (time.time() - start_time) * 1000

print(f"Storage Health Check:")
print(f"  Success: {result.get('success', False)}")
print(f"  Latency: {latency:.2f}ms")
print(f"  Blobs Count: {len(result.get('blobs', []))}")
print(f"  Error: {result.get('error', 'None')}")

# PASS: success=True, latency<500ms
# FAIL: success=False or latency>1000ms
```

#### 1.3 Verificar Operaciones CRUD
```python
# Test upload/download
test_content = "health_check_test"
test_blob_name = "health_check/test.txt"

# Upload test
upload_result = azure_storage.upload_blob(test_blob_name, test_content)
print(f"Upload: {upload_result.get('success', False)}")

# Download test
download_result = azure_storage.download_blob(test_blob_name)
print(f"Download: {download_result.get('success', False)}")

# Cleanup
azure_storage.delete_blob(test_blob_name)
```

### Logs a Verificar
- **PASS**: `"Successfully connected to Azure Storage"`
- **FAIL**: `"Failed to connect to Azure Storage"` o `"Connection timeout"`

## 2. Azure AI Search Health Check

### Comandos de Verificación

#### 2.1 Verificar Configuración
```bash
# Verificar variables de entorno
echo $AZURE_SEARCH_ENDPOINT
echo $AZURE_SEARCH_API_KEY
echo $AZURE_SEARCH_INDEX_NAME

# Verificar desde Python
python -c "
import os
print('AZURE_SEARCH_ENDPOINT:', 'SET' if os.getenv('AZURE_SEARCH_ENDPOINT') else 'NOT SET')
print('AZURE_SEARCH_API_KEY:', 'SET' if os.getenv('AZURE_SEARCH_API_KEY') else 'NOT SET')
print('AZURE_SEARCH_INDEX_NAME:', 'SET' if os.getenv('AZURE_SEARCH_INDEX_NAME') else 'NOT SET')
"
```

#### 2.2 Verificar Conexión y Esquema
```python
# Script de verificación
from utilities.azure_search_client import AzureSearchClient
import time

start_time = time.time()
try:
    client = AzureSearchClient()
    # Test semantic search
    results = client.search_semantic("test", top_k=1)
    latency = (time.time() - start_time) * 1000
    
    print(f"AI Search Health Check:")
    print(f"  Success: True")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Results Count: {len(results)}")
    print(f"  Index Name: {client.index_name}")
    
    # PASS: No exception, latency<1000ms
    # FAIL: Exception or latency>2000ms
    
except Exception as e:
    latency = (time.time() - start_time) * 1000
    print(f"AI Search Health Check:")
    print(f"  Success: False")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Error: {str(e)}")
```

#### 2.3 Verificar Operaciones de Búsqueda
```python
# Test vector search
test_embedding = [0.1] * 1536  # Dummy embedding
results = client.search_vector(test_embedding, top_k=5)
print(f"Vector Search: {len(results)} results")

# Test hybrid search
results = client.search_hybrid("test query", test_embedding, top_k=5)
print(f"Hybrid Search: {len(results)} results")
```

### Logs a Verificar
- **PASS**: `"Successfully connected to Azure AI Search"`
- **FAIL**: `"Failed to connect to Azure AI Search"` o `"Index not found"`

## 3. Redis Health Check

### Comandos de Verificación

#### 3.1 Verificar Configuración
```bash
# Verificar variables de entorno
echo $AZURE_REDIS_URL
echo $AZURE_REDIS_CONNECTIONSTRING
echo $REDIS_TTL_SECS

# Verificar desde Python
python -c "
import os
print('AZURE_REDIS_URL:', 'SET' if os.getenv('AZURE_REDIS_URL') else 'NOT SET')
print('AZURE_REDIS_CONNECTIONSTRING:', 'SET' if os.getenv('AZURE_REDIS_CONNECTIONSTRING') else 'NOT SET')
print('REDIS_TTL_SECS:', os.getenv('REDIS_TTL_SECS', 'NOT SET'))
"
```

#### 3.2 Verificar Conexión
```python
# Script de verificación
from utils.redis_cache import get_cache_stats, _r
import time

start_time = time.time()
stats = get_cache_stats()
latency = (time.time() - start_time) * 1000

print(f"Redis Health Check:")
print(f"  Status: {stats.get('status', 'unknown')}")
print(f"  Latency: {latency:.2f}ms")
print(f"  Total Keys: {stats.get('total_keys', 0)}")
print(f"  Connection Pool Size: {stats.get('connection_pool_size', 'N/A')}")

# Test PING
if _r:
    ping_start = time.time()
    ping_result = _r.ping()
    ping_latency = (time.time() - ping_start) * 1000
    print(f"  PING: {ping_result} ({ping_latency:.2f}ms)")

# PASS: status='active', latency<50ms
# FAIL: status='disabled' or 'error', latency>200ms
```

#### 3.3 Verificar Operaciones Básicas
```python
# Test SET/GET
if _r:
    test_key = "health_check:test"
    test_value = {"test": True, "timestamp": time.time()}
    
    # SET test
    set_result = _r.setex(test_key, 60, str(test_value))
    print(f"SET Test: {set_result}")
    
    # GET test
    get_result = _r.get(test_key)
    print(f"GET Test: {get_result is not None}")
    
    # TTL test
    ttl_result = _r.ttl(test_key)
    print(f"TTL Test: {ttl_result} seconds")
    
    # Cleanup
    _r.delete(test_key)
```

### Logs a Verificar
- **PASS**: `"Redis connection successful"` o `"Cache hit for"`
- **FAIL**: `"Redis connection failed"` o `"Redis URL not configured"`

## 4. Azure OpenAI Health Check

### Comandos de Verificación

#### 4.1 Verificar Configuración
```bash
# Verificar variables de entorno
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY
echo $AZURE_OPENAI_CHAT_DEPLOYMENT
echo $AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT

# Verificar desde Python
python -c "
import os
print('AZURE_OPENAI_ENDPOINT:', 'SET' if os.getenv('AZURE_OPENAI_ENDPOINT') else 'NOT SET')
print('AZURE_OPENAI_API_KEY:', 'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'NOT SET')
print('AZURE_OPENAI_CHAT_DEPLOYMENT:', 'SET' if os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT') else 'NOT SET')
print('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT:', 'SET' if os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT') else 'NOT SET')
"
```

#### 4.2 Verificar Embeddings
```python
# Script de verificación
from apps.embeddings.openai_service import OpenAIService
import time

start_time = time.time()
try:
    service = OpenAIService()
    embedding = service.generate_embedding("health check test")
    latency = (time.time() - start_time) * 1000
    
    print(f"OpenAI Embeddings Health Check:")
    print(f"  Success: True")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Embedding Dimensions: {len(embedding)}")
    print(f"  Is Configured: {service.is_configured}")
    
    # PASS: len(embedding) > 0, latency<2000ms
    # FAIL: Exception or empty embedding, latency>10000ms
    
except Exception as e:
    latency = (time.time() - start_time) * 1000
    print(f"OpenAI Embeddings Health Check:")
    print(f"  Success: False")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Error: {str(e)}")
```

#### 4.3 Verificar Chat Completion
```python
# Test chat completion
messages = [{"role": "user", "content": "Say 'health check ok'"}]
start_time = time.time()

try:
    response = service.generate_chat_response(messages)
    latency = (time.time() - start_time) * 1000
    
    print(f"OpenAI Chat Health Check:")
    print(f"  Success: True")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Response: {response[:50]}...")
    
except Exception as e:
    latency = (time.time() - start_time) * 1000
    print(f"OpenAI Chat Health Check:")
    print(f"  Success: False")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Error: {str(e)}")
```

### Logs a Verificar
- **PASS**: `"Generated embedding with X dimensions"` o `"Chat response generated"`
- **FAIL**: `"Error generating embedding"` o `"Azure OpenAI not configured"`

## 5. Azure Vision Health Check

### Comandos de Verificación

#### 5.1 Verificar Configuración
```bash
# Verificar variables de entorno
echo $VISION_ENDPOINT
echo $VISION_KEY

# Verificar desde Python
python -c "
import os
print('VISION_ENDPOINT:', 'SET' if os.getenv('VISION_ENDPOINT') else 'NOT SET')
print('VISION_KEY:', 'SET' if os.getenv('VISION_KEY') else 'NOT SET')
"
```

#### 5.2 Verificar Conexión
```python
# Script de verificación
from apps.vision.azure_vision_service import AzureVisionService
import time

start_time = time.time()
try:
    service = AzureVisionService()
    # Test OCR with dummy image (or create test image)
    latency = (time.time() - start_time) * 1000
    
    print(f"Azure Vision Health Check:")
    print(f"  Success: True")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Endpoint: {service.endpoint}")
    
    # PASS: No exception, latency<3000ms
    # FAIL: Exception or latency>10000ms
    
except Exception as e:
    latency = (time.time() - start_time) * 1000
    print(f"Azure Vision Health Check:")
    print(f"  Success: False")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Error: {str(e)}")
```

### Logs a Verificar
- **PASS**: `"Azure Vision client initialized"` o `"Text extracted successfully"`
- **FAIL**: `"Failed to initialize Azure Vision client"` o `"OCR extraction failed"`

## 6. WhatsApp/ACS Health Check

### Comandos de Verificación

#### 6.1 Verificar Configuración
```bash
# Verificar variables de entorno
echo $ACS_CONNECTION_STRING
echo $ACS_WHATSAPP_ENDPOINT
echo $ACS_WHATSAPP_API_KEY
echo $ACS_PHONE_NUMBER
echo $WHATSAPP_CHANNEL_ID_GUID

# Verificar desde Python
python -c "
import os
print('ACS_CONNECTION_STRING:', 'SET' if os.getenv('ACS_CONNECTION_STRING') else 'NOT SET')
print('ACS_WHATSAPP_ENDPOINT:', 'SET' if os.getenv('ACS_WHATSAPP_ENDPOINT') else 'NOT SET')
print('ACS_WHATSAPP_API_KEY:', 'SET' if os.getenv('ACS_WHATSAPP_API_KEY') else 'NOT SET')
print('ACS_PHONE_NUMBER:', 'SET' if os.getenv('ACS_PHONE_NUMBER') else 'NOT SET')
print('WHATSAPP_CHANNEL_ID_GUID:', 'SET' if os.getenv('WHATSAPP_CHANNEL_ID_GUID') else 'NOT SET')
"
```

#### 6.2 Verificar Conexión ACS
```python
# Script de verificación
from apps.whatsapp_bot.services import ACSService
import time

start_time = time.time()
try:
    service = ACSService()
    latency = (time.time() - start_time) * 1000
    
    print(f"ACS Health Check:")
    print(f"  Success: True")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Endpoint: {service.endpoint}")
    print(f"  Access Key: {'SET' if service.access_key else 'NOT SET'}")
    
    # PASS: service.endpoint and service.access_key exist
    # FAIL: Missing configuration
    
except Exception as e:
    latency = (time.time() - start_time) * 1000
    print(f"ACS Health Check:")
    print(f"  Success: False")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Error: {str(e)}")
```

#### 6.3 Verificar Endpoint de WhatsApp
```python
# Test WhatsApp endpoint (without sending message)
import requests

endpoint = os.getenv('ACS_WHATSAPP_ENDPOINT')
api_key = os.getenv('ACS_WHATSAPP_API_KEY')

if endpoint and api_key:
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{endpoint}/messages", headers=headers, timeout=10)
        print(f"WhatsApp Endpoint Test:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text[:100]}...")
        
        # PASS: 200, 401, or 403 (endpoint accessible)
        # FAIL: Connection error or 404
        
    except Exception as e:
        print(f"WhatsApp Endpoint Test:")
        print(f"  Error: {str(e)}")
```

### Logs a Verificar
- **PASS**: `"ACS service initialized"` o `"WhatsApp message sent successfully"`
- **FAIL**: `"ACS configuration missing"` o `"Failed to send WhatsApp message"`

## 7. Database Health Check

### Comandos de Verificación

#### 7.1 Verificar Conexión
```python
# Script de verificación
from django.db import connection
import time

start_time = time.time()
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    latency = (time.time() - start_time) * 1000
    
    print(f"Database Health Check:")
    print(f"  Success: True")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Result: {result}")
    
    # PASS: result == (1,), latency<100ms
    # FAIL: Exception or latency>500ms
    
except Exception as e:
    latency = (time.time() - start_time) * 1000
    print(f"Database Health Check:")
    print(f"  Success: False")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Error: {str(e)}")
```

#### 7.2 Verificar Migraciones
```bash
# Verificar migraciones pendientes
python manage.py showmigrations --list

# Verificar estado de migraciones
python manage.py migrate --plan
```

### Logs a Verificar
- **PASS**: `"Database connection successful"` o `"Migration applied successfully"`
- **FAIL**: `"Database connection failed"` o `"Migration failed"`

## 8. Script de Health Check Completo

### 8.1 Script Automatizado
```python
#!/usr/bin/env python3
"""
Health Check Script - VEA Connect Platform
"""

import os
import sys
import time
import json
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

def run_health_checks():
    """Ejecutar todos los health checks."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # 1. Database Check
    print("🔍 Checking Database...")
    start_time = time.time()
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        latency = (time.time() - start_time) * 1000
        results['checks']['database'] = {
            'status': 'PASS',
            'latency_ms': round(latency, 2),
            'message': 'Database connection successful'
        }
        print(f"✅ Database: PASS ({latency:.2f}ms)")
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        results['checks']['database'] = {
            'status': 'FAIL',
            'latency_ms': round(latency, 2),
            'message': str(e)
        }
        print(f"❌ Database: FAIL ({latency:.2f}ms) - {e}")
    
    # 2. Redis Check
    print("🔍 Checking Redis...")
    start_time = time.time()
    try:
        from utils.redis_cache import get_cache_stats
        stats = get_cache_stats()
        latency = (time.time() - start_time) * 1000
        status = 'PASS' if stats.get('status') == 'active' else 'FAIL'
        results['checks']['redis'] = {
            'status': status,
            'latency_ms': round(latency, 2),
            'message': f"Redis status: {stats.get('status')}"
        }
        print(f"{'✅' if status == 'PASS' else '❌'} Redis: {status} ({latency:.2f}ms)")
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        results['checks']['redis'] = {
            'status': 'FAIL',
            'latency_ms': round(latency, 2),
            'message': str(e)
        }
        print(f"❌ Redis: FAIL ({latency:.2f}ms) - {e}")
    
    # 3. Azure Storage Check
    print("🔍 Checking Azure Storage...")
    start_time = time.time()
    try:
        from services.storage_service import azure_storage
        result = azure_storage.list_blobs()
        latency = (time.time() - start_time) * 1000
        status = 'PASS' if result.get('success') else 'FAIL'
        results['checks']['azure_storage'] = {
            'status': status,
            'latency_ms': round(latency, 2),
            'message': f"Storage check: {result.get('success')}"
        }
        print(f"{'✅' if status == 'PASS' else '❌'} Azure Storage: {status} ({latency:.2f}ms)")
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        results['checks']['azure_storage'] = {
            'status': 'FAIL',
            'latency_ms': round(latency, 2),
            'message': str(e)
        }
        print(f"❌ Azure Storage: FAIL ({latency:.2f}ms) - {e}")
    
    # 4. Azure AI Search Check
    print("🔍 Checking Azure AI Search...")
    start_time = time.time()
    try:
        from utilities.azure_search_client import AzureSearchClient
        client = AzureSearchClient()
        results_search = client.search_semantic("test", top_k=1)
        latency = (time.time() - start_time) * 1000
        results['checks']['azure_ai_search'] = {
            'status': 'PASS',
            'latency_ms': round(latency, 2),
            'message': f"Search results: {len(results_search)}"
        }
        print(f"✅ Azure AI Search: PASS ({latency:.2f}ms)")
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        results['checks']['azure_ai_search'] = {
            'status': 'FAIL',
            'latency_ms': round(latency, 2),
            'message': str(e)
        }
        print(f"❌ Azure AI Search: FAIL ({latency:.2f}ms) - {e}")
    
    # 5. Azure OpenAI Check
    print("🔍 Checking Azure OpenAI...")
    start_time = time.time()
    try:
        from apps.embeddings.openai_service import OpenAIService
        service = OpenAIService()
        embedding = service.generate_embedding("test")
        latency = (time.time() - start_time) * 1000
        results['checks']['azure_openai'] = {
            'status': 'PASS',
            'latency_ms': round(latency, 2),
            'message': f"Embedding dimensions: {len(embedding)}"
        }
        print(f"✅ Azure OpenAI: PASS ({latency:.2f}ms)")
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        results['checks']['azure_openai'] = {
            'status': 'FAIL',
            'latency_ms': round(latency, 2),
            'message': str(e)
        }
        print(f"❌ Azure OpenAI: FAIL ({latency:.2f}ms) - {e}")
    
    # 6. ACS/WhatsApp Check
    print("🔍 Checking ACS/WhatsApp...")
    start_time = time.time()
    try:
        from apps.whatsapp_bot.services import ACSService
        service = ACSService()
        latency = (time.time() - start_time) * 1000
        status = 'PASS' if service.endpoint and service.access_key else 'FAIL'
        results['checks']['acs_whatsapp'] = {
            'status': status,
            'latency_ms': round(latency, 2),
            'message': f"ACS configured: {bool(service.endpoint and service.access_key)}"
        }
        print(f"{'✅' if status == 'PASS' else '❌'} ACS/WhatsApp: {status} ({latency:.2f}ms)")
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        results['checks']['acs_whatsapp'] = {
            'status': 'FAIL',
            'latency_ms': round(latency, 2),
            'message': str(e)
        }
        print(f"❌ ACS/WhatsApp: FAIL ({latency:.2f}ms) - {e}")
    
    # Resumen
    total_checks = len(results['checks'])
    passed_checks = sum(1 for check in results['checks'].values() if check['status'] == 'PASS')
    failed_checks = total_checks - passed_checks
    
    print(f"\n📊 Health Check Summary:")
    print(f"   Total Checks: {total_checks}")
    print(f"   Passed: {passed_checks}")
    print(f"   Failed: {failed_checks}")
    print(f"   Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    # Guardar resultados
    with open('health_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == '__main__':
    run_health_checks()
```

### 8.2 Uso del Script
```bash
# Ejecutar health check completo
python scripts/health/health_plan.py

# Ver resultados
cat health_check_results.json
```

## 9. Criterios de Aceptación

### 9.1 PASS Criteria
- ✅ Todos los servicios responden dentro de los umbrales de latencia
- ✅ No hay errores de conexión
- ✅ Configuración completa de variables de entorno
- ✅ Logs muestran operaciones exitosas

### 9.2 FAIL Criteria
- ❌ Algún servicio no responde o falla
- ❌ Latencia excede umbrales críticos
- ❌ Variables de entorno faltantes
- ❌ Errores en logs de conexión

### 9.3 WARNING Criteria
- ⚠️ Latencia cercana a umbrales críticos
- ⚠️ Configuración parcial
- ⚠️ Timeouts ocasionales

## 10. Monitoreo Continuo

### 10.1 Logs a Monitorear
```bash
# Django logs
tail -f logs/django.log | grep -E "(ERROR|WARNING|health)"

# Azure Functions logs
az webapp log tail --name vea-functions-apis --resource-group rg-vea-connect-dev

# Application Insights
# Verificar en Azure Portal > Application Insights > Logs
```

### 10.2 Métricas a Trackear
- Latencia P50 y P95 por servicio
- Tasa de éxito de health checks
- Tiempo de respuesta de endpoints
- Errores por tipo de servicio

---

**Nota**: Este plan no modifica código productivo, solo proporciona herramientas de diagnóstico y verificación.
