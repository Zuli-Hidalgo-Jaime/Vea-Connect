# Fase de Diagnóstico - VEA Connect Platform

## Objetivo
Esta fase establece la línea base (baseline) para el control de cambios en la plataforma VEA Connect, sin modificar código productivo.

## Archivos Generados

### Plantillas de Diagnóstico
- `diagnostico_final.md` - Plantilla para el reporte final de diagnóstico
- `plan_remediacion.md` - Plantilla para el plan de remediación con metodología MoSCoW
- `checklist.md` - Checklist manual para health checks

### Herramientas
- `Makefile` - Targets comentados para futuras fases
- `parches_sugeridos/` - Directorio con correcciones sugeridas (sin aplicar)

## Variables a Auditar

### Azure Storage
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_ACCOUNT_NAME`
- `AZURE_STORAGE_CONTAINER_NAME`

### Azure AI Search
- `AZURE_SEARCH_SERVICE_NAME`
- `AZURE_SEARCH_INDEX_NAME`
- `AZURE_SEARCH_API_KEY`

### Azure OpenAI
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`

### Redis
- `AZURE_REDIS_URL`
- `REDIS_TTL_SECS`

### Django
- `DJANGO_SETTINGS_MODULE`
- `DEBUG`
- `ALLOWED_HOSTS`
- `SECRET_KEY`

## Validación por Fase

### Fase 1: Inventario y Configuración
**Validación**: 
- Verificar presencia de todas las variables requeridas
- Confirmar formatos correctos de connection strings
- Identificar variables duplicadas o redundantes
- Documentar inconsistencias entre entornos

**Criterio de Aceptación**: 
- Lista completa de variables con estado (PRESENTE/FALTANTE)
- Documentación de inconsistencias encontradas

### Fase 2: Health Checks
**Validación**:
- Ejecutar checklist manual de health checks
- Medir latencias de servicios críticos
- Verificar conectividad a todos los servicios Azure
- Documentar endpoints de salud existentes

**Criterio de Aceptación**:
- Checklist completado con resultados
- Métricas de latencia documentadas
- Problemas de conectividad identificados

### Fase 3: Pipeline de Ingesta
**Validación**:
- Probar procesamiento de diferentes tipos de documentos
- Verificar generación de embeddings
- Confirmar indexación en Azure AI Search
- Medir tiempos de procesamiento

**Criterio de Aceptación**:
- Pipeline funcional para todos los tipos de documento
- Métricas de rendimiento documentadas
- Problemas de procesamiento identificados

### Fase 4: Embeddings y Búsqueda
**Validación**:
- Verificar esquema del índice de Azure AI Search
- Probar búsquedas vectoriales y híbridas
- Confirmar configuración de embeddings
- Medir relevancia de resultados

**Criterio de Aceptación**:
- Esquema de índice documentado
- Búsquedas funcionando correctamente
- Métricas de relevancia establecidas

### Fase 5: Redis y Cache
**Validación**:
- Verificar configuración de Redis
- Probar operaciones de cache
- Confirmar TTLs apropiados
- Verificar graceful degradation

**Criterio de Aceptación**:
- Redis operativo y configurado correctamente
- Cache funcionando con TTLs apropiados
- Fallback sin Redis documentado

### Fase 6: Bot y RAG
**Validación**:
- Probar funcionalidad del bot WhatsApp
- Verificar uso de RAG en respuestas
- Confirmar citaciones en respuestas
- Medir tiempos de respuesta

**Criterio de Aceptación**:
- Bot respondiendo correctamente
- RAG integrado y funcionando
- Métricas de respuesta documentadas

### Fase 7: Descarga de Documentos
**Validación**:
- Probar descargas desde Azure Blob Storage
- Probar descargas desde FileSystemStorage
- Verificar generación de SAS URLs
- Confirmar streaming de archivos

**Criterio de Aceptación**:
- Descargas funcionando para ambos storages
- SAS URLs generándose correctamente
- Streaming implementado

### Fase 8: Limpieza y Mantenimiento
**Validación**:
- Ejecutar detección de documentos huérfanos
- Identificar registros rotos en BD
- Detectar claves Redis obsoletas
- Generar reporte de limpieza

**Criterio de Aceptación**:
- Reporte de datos huérfanos generado
- Criterios de limpieza establecidos
- Estimación de espacio a liberar

### Fase 9: Calidad de Código
**Validación**:
- Detectar emojis en código y mensajes
- Identificar docstrings no unificados
- Revisar manejo de errores
- Verificar logging apropiado

**Criterio de Aceptación**:
- Lista de problemas de calidad generada
- Reglas de linter propuestas
- Estándares de código definidos

### Fase 10: Seguridad
**Validación**:
- Verificar gestión de secretos
- Revisar configuración de seguridad
- Identificar exposición de información sensible
- Evaluar políticas de acceso

**Criterio de Aceptación**:
- Riesgos de seguridad documentados
- Recomendaciones de mitigación
- Configuración de seguridad validada

### Fase 11: Tests y DX
**Validación**:
- Revisar cobertura de tests existentes
- Identificar gaps en testing
- Evaluar herramientas de desarrollo
- Proponer mejoras en DX

**Criterio de Aceptación**:
- Estado de tests documentado
- Gaps de testing identificados
- Mejoras de DX propuestas

## Criterios de Aceptación Generales

### PASS
- Todas las fases completadas con documentación
- Problemas identificados y documentados
- Plan de remediación con prioridades establecidas
- Parches sugeridos generados (sin aplicar)
- No se modificó código productivo

### FAIL
- Fases incompletas o sin documentación
- Problemas críticos no identificados
- Modificaciones accidentales a código productivo
- Falta de evidencia para hallazgos

## Próximos Pasos

1. **Completar diagnóstico**: Llenar todas las plantillas con datos reales
2. **Validar hallazgos**: Confirmar problemas identificados
3. **Priorizar acciones**: Usar metodología MoSCoW
4. **Crear PR**: Incluir solo archivos de diagnóstico
5. **Planificar implementación**: Definir fases de remediación

---

**Documento generado automáticamente - Actualizar según avances**
