
# Diagnóstico End-to-End VEA Connect

**Fecha:** 2025-08-10 22:38:46
**UUID de prueba:** a8f92a46

## Resumen
- **Total:** 9 servicios
- **✅ Exitosos:** 7
- **⚠️ Advertencias:** 0
- **❌ Fallidos:** 2

## Resultados Detallados

| Servicio | Estado | Latencia(ms) | Nota |
|----------|--------|--------------|------|
| Redis | ❌ | 0 | Conexión apunta a localhost - no hay conexión externa configurada |
| Azure Storage | ✅ | 54 | Archivo diag-a8f92a46.txt procesado |
| Azure Vision | ✅ | 812 | Cliente inicializado y conectado |
| Azure OpenAI | ✅ | 991 | Chat: 'Ok', Embedding: 1536 dimensiones |
| Azure AI Search | ✅ | 57 | Documento a8f92a46 procesado |
| ACS WhatsApp | ✅ | 105 | Cliente inicializado y credenciales válidas |
| Application Insights | ✅ | 0 | Connection string válida |
| Django | ✅ | 3201 | Sin migraciones pendientes |
| Functions Health | ❌ | 35 | GET falló: HTTPSConnectionPool(host='vea-connect-functions.azurewebsites.net', port=443): Max retries exceeded with url: /api/health (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000001A18A1ABD30>: Failed to resolve 'vea-connect-functions.azurewebsites.net' ([Errno 11001] getaddrinfo failed)")) |

## Sugerencias

### Servicios que requieren atención:
- **Redis**: Conexión apunta a localhost - no hay conexión externa configurada
- **Functions Health**: GET falló: HTTPSConnectionPool(host='vea-connect-functions.azurewebsites.net', port=443): Max retries exceeded with url: /api/health (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000001A18A1ABD30>: Failed to resolve 'vea-connect-functions.azurewebsites.net' ([Errno 11001] getaddrinfo failed)"))


## Recursos temporales creados
- blob:diag-a8f92a46.txt
- search_doc:diag-a8f92a46
