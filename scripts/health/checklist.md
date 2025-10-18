# Health Check Checklist - VEA Connect Platform

## Pre-requisitos
- [ ] Acceso a Azure Portal
- [ ] Credenciales de desarrollo configuradas
- [ ] Herramientas de línea de comandos instaladas (Azure CLI, Python, etc.)
- [ ] Acceso a logs de la aplicación

## 1. Verificación de Configuración

### Variables de Entorno
- [ ] Verificar presencia de variables críticas en `local.settings.json`
- [ ] Validar formato de connection strings
- [ ] Confirmar que no hay valores hardcodeados en logs
- [ ] Verificar que las variables de entorno están siendo cargadas correctamente

### Configuración de Django
- [ ] Confirmar `DJANGO_SETTINGS_MODULE` está configurado
- [ ] Verificar `DEBUG` está en `False` en producción
- [ ] Validar `ALLOWED_HOSTS` incluye dominios correctos
- [ ] Confirmar `SECRET_KEY` está configurado y es seguro

## 2. Health Checks de Infraestructura

### Azure Storage
- [ ] Verificar conexión al storage account
- [ ] Listar blobs en el contenedor principal
- [ ] Probar upload de archivo de prueba (1KB)
- [ ] Probar download del archivo de prueba
- [ ] Verificar generación de SAS URLs
- [ ] Medir latencia de operaciones (objetivo: < 500ms)

### Azure AI Search
- [ ] Verificar conexión al servicio de búsqueda
- [ ] Confirmar que el índice existe
- [ ] Validar esquema del índice
- [ ] Probar búsqueda simple
- [ ] Probar búsqueda vectorial
- [ ] Medir latencia de búsquedas (objetivo: < 1000ms)

### Redis
- [ ] Verificar conexión a Redis
- [ ] Probar operación PING
- [ ] Probar SET/GET de clave temporal
- [ ] Verificar TTL de claves
- [ ] Confirmar namespacing de claves
- [ ] Medir latencia de Redis (objetivo: < 50ms)

### Azure OpenAI
- [ ] Verificar conexión al endpoint
- [ ] Probar llamada de embeddings
- [ ] Probar llamada de chat
- [ ] Verificar límites de rate limiting
- [ ] Medir latencia de OpenAI (objetivo: < 2000ms)

## 3. Health Checks de Aplicación

### Django Web App
- [ ] Verificar que la aplicación responde en `/`
- [ ] Probar endpoint `/healthz` (si existe)
- [ ] Verificar que los archivos estáticos se sirven
- [ ] Probar autenticación de usuarios
- [ ] Verificar logs de aplicación

### Azure Functions
- [ ] Verificar que las funciones están desplegadas
- [ ] Probar trigger de WhatsApp Event Grid
- [ ] Verificar logs de funciones
- [ ] Probar health check de funciones (si existe)

## 4. Pipeline de Ingesta

### Procesamiento de Documentos
- [ ] Subir documento PDF de prueba
- [ ] Verificar que se procesa correctamente
- [ ] Confirmar que se generan embeddings
- [ ] Verificar que se indexa en Azure AI Search
- [ ] Medir tiempo total de procesamiento

### Procesamiento de Imágenes
- [ ] Subir imagen JPG/PNG de prueba
- [ ] Verificar que se ejecuta OCR
- [ ] Confirmar extracción de texto
- [ ] Verificar que se generan embeddings
- [ ] Medir tiempo de procesamiento de imagen

## 5. Bot y RAG

### Funcionalidad del Bot
- [ ] Enviar mensaje de prueba a WhatsApp
- [ ] Verificar que el bot responde
- [ ] Confirmar que usa RAG para respuestas
- [ ] Verificar citaciones en respuestas
- [ ] Medir tiempo de respuesta del bot

### Búsqueda Semántica
- [ ] Probar consulta simple
- [ ] Probar consulta compleja
- [ ] Verificar relevancia de resultados
- [ ] Confirmar que se usan embeddings
- [ ] Verificar cache de resultados

## 6. Descarga de Documentos

### Azure Blob Storage
- [ ] Probar descarga de documento desde Azure
- [ ] Verificar generación de SAS URL
- [ ] Confirmar que la URL expira correctamente
- [ ] Probar con diferentes tipos de archivo

### FileSystemStorage
- [ ] Probar descarga de documento local
- [ ] Verificar streaming de archivos
- [ ] Confirmar que no se cargan en memoria
- [ ] Probar con archivos grandes

## 7. Monitoreo y Logs

### Logs de Aplicación
- [ ] Verificar que los logs se generan
- [ ] Confirmar que no contienen información sensible
- [ ] Verificar niveles de log apropiados
- [ ] Confirmar formato structured JSON

### Métricas
- [ ] Verificar métricas de latencia
- [ ] Confirmar métricas de errores
- [ ] Verificar métricas de cache hit rate
- [ ] Confirmar métricas de throughput

## 8. Seguridad

### Gestión de Secretos
- [ ] Verificar que no hay secretos en logs
- [ ] Confirmar uso de Key Vault
- [ ] Verificar rotación de claves
- [ ] Confirmar permisos mínimos

### Configuración de Seguridad
- [ ] Verificar CORS configurado correctamente
- [ ] Confirmar validación de MIME types
- [ ] Verificar políticas de SAS
- [ ] Confirmar HTTPS en producción

## 9. Performance

### Latencia
- [ ] Medir latencia P50 de endpoints críticos
- [ ] Medir latencia P95 de endpoints críticos
- [ ] Verificar que están dentro de objetivos
- [ ] Identificar cuellos de botella

### Throughput
- [ ] Probar carga de múltiples usuarios
- [ ] Verificar que el sistema escala
- [ ] Confirmar que no hay degradación
- [ ] Medir capacidad máxima

## 10. Limpieza y Mantenimiento

### Documentos Huérfanos
- [ ] Ejecutar script de detección de huérfanos
- [ ] Revisar reporte de blobs huérfanos
- [ ] Verificar registros rotos en BD
- [ ] Revisar claves Redis obsoletas

### Cache
- [ ] Verificar estadísticas de Redis
- [ ] Confirmar TTLs apropiados
- [ ] Verificar limpieza automática
- [ ] Medir hit rate del cache

## Criterios de Aceptación

### Todos los checks deben pasar:
- [ ] Configuración válida
- [ ] Infraestructura operativa
- [ ] Aplicación respondiendo
- [ ] Pipeline funcionando
- [ ] Bot operativo
- [ ] Descargas funcionando
- [ ] Logs apropiados
- [ ] Seguridad verificada
- [ ] Performance aceptable
- [ ] Mantenimiento al día

## Reporte de Health Check

### Resumen
- **Fecha**: [FECHA]
- **Ejecutado por**: [NOMBRE]
- **Estado General**: [PASS/FAIL]
- **Checks Pasados**: [X/Y]
- **Checks Fallidos**: [X/Y]

### Problemas Encontrados
1. [PROBLEMA_1] - [SEVERIDAD] - [ACCION_REQUERIDA]
2. [PROBLEMA_2] - [SEVERIDAD] - [ACCION_REQUERIDA]

### Recomendaciones
1. [RECOMENDACION_1]
2. [RECOMENDACION_2]

### Próximo Health Check
- **Fecha Programada**: [FECHA]
- **Responsable**: [NOMBRE]

---

**Checklist generado automáticamente - Completar manualmente durante ejecución**
