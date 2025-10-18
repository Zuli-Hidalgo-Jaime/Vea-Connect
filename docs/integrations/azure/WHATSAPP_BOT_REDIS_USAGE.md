# WhatsApp Bot - Uso de Redis

## Resumen

El WhatsApp Bot utiliza Redis **exclusivamente** para el manejo del contexto conversacional. Esta es la única funcionalidad en toda la aplicación que requiere Redis.

## Propósito del Uso de Redis

### Contexto Conversacional
- **Almacenamiento temporal**: Guarda el estado de la conversación por número de teléfono
- **TTL configurable**: Por defecto 1 hora (3600 segundos)
- **Actualización incremental**: Permite agregar nueva información al contexto existente
- **Recuperación de contexto**: Para mantener conversaciones coherentes entre mensajes

### Ejemplo de Uso
```python
# El WhatsApp Bot guarda información como:
context_data = {
    'last_intent': 'donations',
    'customer_name': 'Juan Pérez',
    'ministry_name': 'Ministerio de Educación',
    'conversation_step': 'waiting_for_confirmation'
}
```

## Configuración

### Variable de Entorno Requerida
```bash
# Solo necesaria si se desea usar Redis para contexto conversacional
AZURE_REDIS_CONNECTIONSTRING=your-redis-connection-string
```

### Configuración de Django
```python
# config/settings/production.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
```

## Comportamiento por Defecto

### Sin Redis Configurado
- El WhatsApp Bot usa `LocMemCache` (caché en memoria)
- El contexto se pierde al reiniciar la aplicación
- Funcionalidad completa del bot se mantiene

### Con Redis Configurado
- El WhatsApp Bot usa Redis para contexto persistente
- El contexto sobrevive reinicios de aplicación
- Mejor para conversaciones largas o complejas

## Ubicación del Código

### Archivos Principales
- `apps/whatsapp_bot/services.py` - Clase `LoggingService`
- `apps/whatsapp_bot/event_grid_handler.py` - Manejo de contexto

### Métodos Clave
```python
# En LoggingService:
- save_context_to_redis()    # Guardar contexto
- get_context_from_redis()   # Recuperar contexto
- update_context()           # Actualizar contexto
```

## Consideraciones de Seguridad

### Datos Almacenados
- Solo información de contexto conversacional
- No datos sensibles del usuario
- TTL automático para limpieza

### Acceso
- Solo desde el módulo `apps/whatsapp_bot`
- No accesible desde otras partes de la aplicación
- Logs de acceso para auditoría

## Monitoreo

### Métricas Importantes
- Tiempo de respuesta de Redis
- Tasa de hit/miss del contexto
- Uso de memoria de Redis

### Logs
```python
logger.info(f"Saved context to cache for {phone_number}")
logger.info(f"Retrieved context from cache for {phone_number}")
logger.error(f"Error getting context from cache: {str(e)}")
```

## Migración

### De LocMemCache a Redis
1. Configurar `AZURE_REDIS_CONNECTIONSTRING`
2. Cambiar backend de caché en settings
3. Reiniciar aplicación

### De Redis a LocMemCache
1. Eliminar `AZURE_REDIS_CONNECTIONSTRING`
2. Verificar configuración de caché
3. Reiniciar aplicación

## Troubleshooting

### Problemas Comunes
1. **Timeout de conexión**: Verificar configuración de Redis
2. **Contexto perdido**: Verificar TTL y configuración
3. **Errores de caché**: Revisar logs del WhatsApp Bot

### Diagnóstico
```python
# Verificar estado de caché
from django.core.cache import cache
cache.set('test_key', 'test_value', 60)
result = cache.get('test_key')
print(f"Cache test: {result}")
```

## Conclusión

Redis en el WhatsApp Bot es **opcional** y solo se usa para mejorar la experiencia conversacional. La aplicación funciona completamente sin Redis, pero con capacidades limitadas de contexto. 