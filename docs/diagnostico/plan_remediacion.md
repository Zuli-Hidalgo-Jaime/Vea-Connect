# Plan de Remediación - Unificación de Configuración

## Resumen Ejecutivo

Este documento describe el plan para unificar la configuración de VEA Connect mediante un adaptador de configuración que mantiene compatibilidad con variables legacy mientras proporciona una interfaz unificada y segura.

## Objetivos

1. **Unificar acceso a configuración** sin romper código existente
2. **Mantener compatibilidad** con variables legacy (BLOB_*)
3. **Implementar precedencia clara** ENV > AZURE_* > BLOB_* > DEFAULT
4. **Proporcionar logging seguro** sin exponer valores sensibles
5. **Habilitar migración gradual** mediante feature flag

## Arquitectura del Adaptador

### Precedencia de Configuración
```
1. os.environ (máxima prioridad)
2. settings.AZURE_* (configuración moderna)
3. settings.BLOB_* (configuración legacy)
4. Valores por defecto (mínima prioridad)
```

### Feature Flag
- **CONFIG_ADAPTER_ENABLED**: Controla si el adaptador está activo
- **Por defecto**: `False` (no afecta runtime actual)
- **Activación**: Variable de entorno `CONFIG_ADAPTER_ENABLED=True`

## Mapeo de Variables Legacy → Unificadas

### Azure Storage

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| `BLOB_ACCOUNT_NAME` | `AZURE_STORAGE_ACCOUNT_NAME` | `get_storage_account_name()` | Nombre de cuenta de storage |
| `BLOB_ACCOUNT_KEY` | `AZURE_STORAGE_ACCOUNT_KEY` | `get_storage_account_key()` | Clave de cuenta de storage |
| `BLOB_CONTAINER_NAME` | `AZURE_CONTAINER` | `get_storage_container()` | Nombre del contenedor |
| - | `AZURE_STORAGE_CONNECTION_STRING` | `get_storage_connection_string()` | Connection string completa |

### Azure AI Search

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `AZURE_SEARCH_ENDPOINT` | `get_search_service()` | Endpoint del servicio |
| - | `AZURE_SEARCH_API_KEY` | `get_search_key()` | Clave de API |
| - | `AZURE_SEARCH_INDEX_NAME` | `get_search_index()` | Nombre del índice |

### Azure OpenAI

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `AZURE_OPENAI_ENDPOINT` | `get_openai_endpoint()` | Endpoint del servicio |
| - | `AZURE_OPENAI_API_KEY` | `get_openai_api_key()` | Clave de API |
| - | `AZURE_OPENAI_CHAT_DEPLOYMENT` | `get_openai_chat_deployment()` | Deployment de chat |
| - | `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` | `get_openai_embeddings_deployment()` | Deployment de embeddings |

### Azure Computer Vision

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `VISION_ENDPOINT` | `get_vision_endpoint()` | Endpoint del servicio |
| - | `VISION_KEY` | `get_vision_key()` | Clave de API |

### Azure Communication Services

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `ACS_CONNECTION_STRING` | `get_acs_connection_string()` | Connection string de ACS |
| - | `ACS_WHATSAPP_API_KEY` | `get_acs_whatsapp_api_key()` | Clave de API de WhatsApp |
| - | `ACS_WHATSAPP_ENDPOINT` | `get_acs_whatsapp_endpoint()` | Endpoint de WhatsApp |
| - | `ACS_PHONE_NUMBER` | `get_acs_phone_number()` | Número de teléfono |

### Base de Datos

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `DATABASE_URL` | `get_database_url()` | URL de conexión |
| - | `AZURE_POSTGRESQL_NAME` | `get_postgresql_name()` | Nombre de la BD |
| - | `AZURE_POSTGRESQL_USERNAME` | `get_postgresql_username()` | Usuario de la BD |
| - | `AZURE_POSTGRESQL_PASSWORD` | `get_postgresql_password()` | Contraseña de la BD |
| - | `AZURE_POSTGRESQL_HOST` | `get_postgresql_host()` | Host de la BD |
| - | `DB_PORT` | `get_postgresql_port()` | Puerto de la BD |

### Azure Functions

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `FUNCTION_APP_URL` | `get_function_app_url()` | URL de la Function App |
| - | `FUNCTION_APP_KEY` | `get_function_app_key()` | Clave de la Function App |

### Application Insights

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `APPLICATIONINSIGHTS_CONNECTION_STRING` | `get_application_insights_connection_string()` | Connection string de App Insights |

### Queue

| Variable Legacy | Variable Moderna | Función Adaptador | Descripción |
|----------------|------------------|-------------------|-------------|
| - | `QUEUE_NAME` | `get_queue_name()` | Nombre de la cola |

## Implementación del Adaptador

### Archivo Principal
- **Ubicación**: `config/settings/config_adapter.py`
- **Funcionalidad**: Proporciona funciones unificadas para acceder a configuración
- **Logging**: Solo registra origen (ENV/SETTINGS/LEGACY), nunca valores

### Funciones Principales

#### Función Base de Precedencia
```python
def _get_config_with_precedence(
    env_var: str,
    azure_setting: str,
    legacy_setting: Optional[str] = None,
    default: Optional[str] = None
) -> Optional[str]:
```

#### Funciones de Acceso por Servicio
- `get_storage_account_name()` - Nombre de cuenta de storage
- `get_storage_account_key()` - Clave de cuenta de storage
- `get_storage_container()` - Contenedor de storage
- `get_search_service()` - Endpoint de Azure AI Search
- `get_openai_endpoint()` - Endpoint de Azure OpenAI
- `get_vision_endpoint()` - Endpoint de Computer Vision
- `get_acs_connection_string()` - Connection string de ACS

#### Funciones de Utilidad
- `get_config_status()` - Estado de todas las configuraciones
- `validate_required_configs()` - Validación de configuraciones requeridas
- `is_config_adapter_enabled()` - Verificar si el adaptador está activo

## Estrategia de Migración

### Fase 1: Implementación (Completada)
- ✅ Crear adaptador de configuración
- ✅ Implementar feature flag (OFF por defecto)
- ✅ Documentar mapeo de variables
- ✅ Crear funciones de acceso unificadas

### Fase 2: Pruebas (Pendiente)
- [ ] Crear módulos de prueba que usen el adaptador
- [ ] Validar funcionamiento con variables legacy
- [ ] Verificar precedencia de configuración
- [ ] Probar logging seguro

### Fase 3: Migración Gradual (Pendiente)
- [ ] Identificar módulos candidatos para migración
- [ ] Migrar módulos nuevos primero
- [ ] Migrar módulos existentes uno por uno
- [ ] Validar funcionamiento en cada paso

### Fase 4: Limpieza (Pendiente)
- [ ] Migrar todos los módulos al adaptador
- [ ] Eliminar variables legacy obsoletas
- [ ] Actualizar documentación
- [ ] Optimizar configuración

## Beneficios Esperados

### Seguridad
- **Logging seguro**: No expone valores sensibles
- **Control centralizado**: Un solo punto de acceso a configuración
- **Auditoría**: Trazabilidad del origen de cada configuración

### Mantenibilidad
- **Código limpio**: Interfaz unificada y consistente
- **Compatibilidad**: No rompe código existente
- **Flexibilidad**: Fácil agregar nuevas configuraciones

### Operaciones
- **Debugging**: Identificación rápida de problemas de configuración
- **Monitoreo**: Estado de configuración en tiempo real
- **Despliegue**: Configuración consistente entre entornos

## Riesgos y Mitigaciones

### Riesgo: Breaking Changes
**Mitigación**: Feature flag OFF por defecto, migración gradual

### Riesgo: Performance Overhead
**Mitigación**: Logging solo en DEBUG, cache de configuración

### Riesgo: Configuración Inconsistente
**Mitigación**: Precedencia clara, validación de configuraciones

### Riesgo: Complejidad Adicional
**Mitigación**: Documentación clara, ejemplos de uso

## Criterios de Éxito

### Técnicos
- [ ] Adaptador funciona sin afectar runtime actual
- [ ] Precedencia de configuración funciona correctamente
- [ ] Logging seguro no expone valores sensibles
- [ ] Feature flag controla activación del adaptador

### Funcionales
- [ ] Compatibilidad total con variables legacy
- [ ] Interfaz unificada para nuevas configuraciones
- [ ] Documentación completa y actualizada
- [ ] Ejemplos de uso disponibles

### Operacionales
- [ ] Migración gradual sin interrupciones
- [ ] Monitoreo de configuración disponible
- [ ] Rollback simple si es necesario
- [ ] Capacitación del equipo completada

## Próximos Pasos

1. **Validar implementación** en entorno de desarrollo
2. **Crear módulos de prueba** que usen el adaptador
3. **Documentar casos de uso** específicos
4. **Planificar migración** de módulos existentes
5. **Establecer métricas** de éxito

## Rollback Plan

En caso de problemas:

1. **Desactivar feature flag**: `CONFIG_ADAPTER_ENABLED=False`
2. **Eliminar archivo**: `config/settings/config_adapter.py`
3. **Revertir cambios**: Eliminar feature flag de settings
4. **Verificar funcionamiento**: Confirmar que todo funciona como antes

El rollback es simple y no afecta la configuración existente.

---

# Fase 5: Capa de Cache Redis Optimizada

## Resumen

Se ha implementado una capa de cache Redis optimizada con graceful degradation, namespacing y feature flag para mejorar el rendimiento sin afectar la funcionalidad existente.

## Características Implementadas

### ✅ Graceful Degradation
- Si Redis no está disponible → retorna `None` sin excepción
- Si feature flag está deshabilitado → cache deshabilitado
- Timeouts configurados para evitar bloqueos

### ✅ Namespacing Optimizado
- `vea:emb:*` - Embeddings (TTL: 3600s)
- `vea:ans:*` - Respuestas AI Search (TTL: 1800s)  
- `vea:sas:*` - SAS Tokens (TTL: 300s)

### ✅ TTLs Específicos por Tipo
- **Embeddings**: 1 hora (datos estables)
- **AI Search**: 30 minutos (respuestas semánticas)
- **SAS Tokens**: 5 minutos (tokens temporales)

### ✅ Feature Flag
- `CACHE_LAYER_ENABLED=False` (OFF por defecto)
- Control granular sin impacto en runtime

## Funciones Disponibles

### Cache de Embeddings
```python
from utils.cache_layer import get_emb, set_emb

# Obtener embedding desde cache
embedding = get_emb("texto para buscar")

# Guardar embedding en cache
success = set_emb("texto", embedding_list, ttl=3600)
```

### Cache de AI Search
```python
from utils.cache_layer import get_ans, set_ans

# Obtener respuesta desde cache
response = get_ans("query de búsqueda")

# Guardar respuesta en cache
success = set_ans("query", response_dict, ttl=1800)
```

### Cache de SAS Tokens
```python
from utils.cache_layer import get_sas, set_sas

# Obtener SAS token desde cache
token = get_sas("container", "blob_name")

# Guardar SAS token en cache
success = set_sas("container", "blob_name", "token", ttl=300)
```

### Utilidades
```python
from utils.cache_layer import (
    get_cache_stats,    # Estadísticas del cache
    clear_cache,        # Limpiar cache (todo o por namespace)
    is_cache_enabled,   # Verificar si está habilitado
    get_cache_health    # Estado de salud del cache
)
```

## Migración Módulo a Módulo

### 1. Módulos de Embeddings
**Archivos afectados:**
- `apps/embeddings/views.py`
- `apps/embeddings/services.py`
- `functions/create_embedding/__init__.py`

**Cambios sugeridos:**
```python
# ANTES
from utils.redis_cache import get_emb, set_emb

# DESPUÉS (cuando se habilite el feature flag)
from utils.cache_layer import get_emb, set_emb
```

### 2. Módulos de AI Search
**Archivos afectados:**
- `apps/embeddings/views.py`
- `functions/search_similar/__init__.py`

**Cambios sugeridos:**
```python
# ANTES
# Sin cache específico para AI Search

# DESPUÉS (cuando se habilite el feature flag)
from utils.cache_layer import get_ans, set_ans

# En funciones de búsqueda
cached_response = get_ans(query)
if cached_response:
    return cached_response

# Realizar búsqueda y cachear resultado
response = perform_search(query)
set_ans(query, response)
return response
```

### 3. Módulos de Storage
**Archivos afectados:**
- `storage/backends.py`
- `utils/azureblobstorage.py`

**Cambios sugeridos:**
```python
# ANTES
# Generar SAS token cada vez

# DESPUÉS (cuando se habilite el feature flag)
from utils.cache_layer import get_sas, set_sas

# Verificar cache antes de generar
cached_token = get_sas(container, blob_name)
if cached_token:
    return cached_token

# Generar y cachear
token = generate_sas_token(container, blob_name)
set_sas(container, blob_name, token)
return token
```

## Configuración

### Feature Flag
```python
# config/settings/base.py
CACHE_LAYER_ENABLED = os.environ.get('CACHE_LAYER_ENABLED', 'False') == 'True'
```

### Variables de Entorno
```bash
# Habilitar capa de cache
CACHE_LAYER_ENABLED=True

# URL de Redis (una de estas)
AZURE_REDIS_URL=redis://host:port
AZURE_REDIS_CONNECTIONSTRING=redis://host:port
REDIS_URL=redis://host:port
```

### TTLs Personalizados
```python
from utils.cache_layer import set_ttl_defaults

# Configurar TTLs personalizados
set_ttl_defaults(
    emb_ttl=7200,  # 2 horas para embeddings
    ans_ttl=3600,  # 1 hora para AI Search
    sas_ttl=600    # 10 minutos para SAS tokens
)
```

## Monitoreo y Debugging

### Estado del Cache
```python
from utils.cache_layer import get_cache_health, get_cache_stats

# Verificar salud del cache
health = get_cache_health()
print(f"Cache status: {health['status']}")

# Obtener estadísticas
stats = get_cache_stats()
print(f"Embeddings cached: {stats['keyspace']['vea:emb']}")
```

### Logging
```python
import logging
logging.getLogger('utils.cache_layer').setLevel(logging.DEBUG)
```

## Rollback

Para hacer rollback de la capa de cache:

1. **Eliminar archivo**: `utils/cache_layer.py`
2. **Remover feature flag**: Eliminar `CACHE_LAYER_ENABLED` de `config/settings/base.py`
3. **Limpiar imports**: Remover cualquier import de `utils.cache_layer` en módulos nuevos

El rollback es simple y no afecta el cache existente de Django.
