# Herramientas de Limpieza de Datos Huérfanos

Este directorio contiene herramientas para auditar y limpiar datos huérfanos en el sistema VeaConnect.

## Archivos

### `orphans_audit.py`
Script principal para auditar datos huérfanos en modo dry-run por defecto.

### `example_usage.py`
Script de ejemplo que demuestra cómo usar las herramientas programáticamente.

### `README.md`
Este archivo de documentación.

## Uso Rápido

### Auditoría Básica (Dry-Run)
```bash
# Ejecutar auditoría con configuración por defecto (30 días)
python scripts/cleanup/orphans_audit.py

# Ejecutar con logging detallado
python scripts/cleanup/orphans_audit.py --verbose

# Ejecutar con umbral personalizado (60 días)
python scripts/cleanup/orphans_audit.py --days 60
```

### Limpieza Real (¡Usar con Precaución!)
```bash
# Ejecutar limpieza real (requiere confirmación)
python scripts/cleanup/orphans_audit.py --force

# Limpieza con umbral personalizado
python scripts/cleanup/orphans_audit.py --force --days 60
```

### Ejemplos Programáticos
```bash
# Ejecutar ejemplos de uso
python scripts/cleanup/example_usage.py
```

## Tipos de Datos Auditados

### 1. Blobs Huérfanos (Azure Storage)
- **Descripción**: Archivos en Azure Blob Storage sin referencia en la base de datos
- **Criterios**: Blobs más antiguos de 30 días sin registro en `Document`
- **Riesgo**: Bajo

### 2. Documentos Huérfanos (Base de Datos)
- **Descripción**: Registros en `Document` que referencian blobs inexistentes
- **Criterios**: Documentos que apuntan a blobs que ya no existen
- **Riesgo**: Medio

### 3. Contactos Huérfanos (Base de Datos)
- **Descripción**: Contactos muy antiguos sin actividad reciente
- **Criterios**: Contactos creados hace más de 30 días sin actualizaciones
- **Riesgo**: Bajo

### 4. Claves Redis Huérfanas (Cache)
- **Descripción**: Claves de cache sin TTL configurado
- **Criterios**: Claves con patrones específicos sin expiración
- **Riesgo**: Bajo

### 5. Documentos de Búsqueda Huérfanos (Azure AI Search)
- **Descripción**: Documentos en el índice sin correspondencia en BD
- **Criterios**: Pendiente de implementación
- **Riesgo**: Bajo

## Opciones de Línea de Comandos

### `orphans_audit.py`

| Opción | Descripción | Por Defecto |
|--------|-------------|-------------|
| `--force` | Realizar eliminación real (no dry-run) | `False` |
| `--days DAYS` | Umbral de días para considerar huérfanos | `30` |
| `--verbose` | Habilitar logging detallado | `False` |
| `--output PATH` | Ruta personalizada para el reporte | Auto-generada |

### Ejemplos de Uso

```bash
# Dry-run básico
python scripts/cleanup/orphans_audit.py

# Dry-run con umbral de 60 días y logging detallado
python scripts/cleanup/orphans_audit.py --days 60 --verbose

# Limpieza real con confirmación
python scripts/cleanup/orphans_audit.py --force

# Exportar reporte con nombre personalizado
python scripts/cleanup/orphans_audit.py --output logs/audit_custom.json
```

## Reportes Generados

### Formato del Reporte
Los reportes se generan en formato JSON con la siguiente estructura:

```json
{
  "timestamp": "2025-08-12T11:07:20.875436",
  "dry_run": true,
  "days_threshold": 30,
  "cutoff_date": "2025-07-13T17:07:20.875436+00:00",
  "summary": {
    "total_orphaned_items": 0,
    "orphaned_blobs": 0,
    "orphaned_documents": 0,
    "orphaned_contacts": 0,
    "orphaned_redis_keys": 0,
    "orphaned_search_documents": 0
  },
  "details": {
    "orphaned_blobs": [...],
    "orphaned_documents": [...],
    "orphaned_contacts": [...],
    "orphaned_redis_keys": [...],
    "orphaned_search_documents": [...]
  }
}
```

### Ubicación de Reportes
- **Por defecto**: `logs/cleanup_report_YYYYMMDD_HHMMSS.json`
- **Personalizada**: Especificada con `--output`

## Uso Programático

### Ejemplo Básico
```python
from scripts.cleanup.orphans_audit import OrphanedDataAuditor

# Crear auditor
auditor = OrphanedDataAuditor(
    dry_run=True,
    days_threshold=30,
    verbose=True
)

# Ejecutar auditoría
results = auditor.run_audit()

# Exportar reporte
report_path = auditor.export_report()

print(f"Total huérfanos: {results['summary']['total_orphaned_items']}")
```

### Ejemplo con Limpieza
```python
# Crear auditor para limpieza real
auditor = OrphanedDataAuditor(
    dry_run=False,  # ¡CUIDADO! Esto eliminará datos reales
    days_threshold=60
)

# Ejecutar auditoría y limpieza
results = auditor.run_audit()

print(f"Elementos eliminados: {results['summary']['total_orphaned_items']}")
```

## Configuración Requerida

### Variables de Entorno
```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@host:port/db

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_storage_key
AZURE_STORAGE_CONTAINER_NAME=documents

# Redis
REDIS_URL=redis://host:port

# Azure AI Search
AZURE_SEARCH_SERVICE_NAME=your_search_service
AZURE_SEARCH_API_KEY=your_search_key
```

### Manejo de Configuración Faltante
El script maneja graciosamente la falta de configuración:
- **Azure no disponible**: Salta auditoría de blobs
- **Redis no disponible**: Salta auditoría de cache
- **Base de datos no configurada**: Salta auditorías de BD

## Proceso de Verificación Manual

### Antes de la Limpieza
1. **Ejecutar dry-run**: `python scripts/cleanup/orphans_audit.py --verbose`
2. **Revisar reporte**: Verificar elementos listados
3. **Verificación manual**: Seguir pasos en `docs/diagnostico/cleanup_plan.md`
4. **Backup**: Crear backup de datos críticos
5. **Notificación**: Informar a usuarios sobre mantenimiento

### Durante la Limpieza
1. **Monitoreo**: Supervisar logs y métricas
2. **Pruebas**: Verificar funcionalidades críticas
3. **Documentación**: Registrar cualquier problema

### Después de la Limpieza
1. **Verificación**: Ejecutar auditoría post-limpieza
2. **Pruebas**: Verificar funcionalidad completa
3. **Documentación**: Actualizar métricas y registros

## Consideraciones de Seguridad

### Modo Dry-Run
- **Por defecto**: El script ejecuta en modo dry-run
- **Sin cambios**: No modifica datos reales
- **Solo reporte**: Genera reporte de elementos huérfanos

### Modo Force
- **Confirmación requerida**: Solicita confirmación explícita
- **Advertencias**: Muestra advertencias claras
- **Logging detallado**: Registra todas las operaciones

### Validaciones
- **Verificación de entorno**: Confirma configuración antes de ejecutar
- **Verificación de permisos**: Valida acceso a servicios
- **Rollback plan**: Documenta procedimientos de rollback

## Monitoreo Continuo

### Auditoría Programada
```bash
# Crear script de auditoría programada
cat > scripts/cleanup/scheduled_audit.sh << 'EOF'
#!/bin/bash
cd /path/to/veaconnect-webapp-prod
python scripts/cleanup/orphans_audit.py --days 30 --output logs/scheduled_audit_$(date +%Y%m%d).json
EOF

chmod +x scripts/cleanup/scheduled_audit.sh

# Agregar a crontab (semanal)
# 0 2 * * 0 /path/to/veaconnect-webapp-prod/scripts/cleanup/scheduled_audit.sh
```

### Alertas
- **Espacio de almacenamiento**: Monitorear uso de Azure Storage
- **Tamaño de base de datos**: Monitorear crecimiento de tablas
- **Uso de cache**: Monitorear uso de Redis

## Troubleshooting

### Problemas Comunes

#### Error de Importación
```
ModuleNotFoundError: No module named 'documents'
```
**Solución**: Verificar que el script se ejecuta desde el directorio raíz del proyecto.

#### Error de Configuración de Base de Datos
```
settings.DATABASES is improperly configured
```
**Solución**: Configurar `DATABASE_URL` o verificar configuración de Django.

#### Error de Azure Storage
```
Azure Storage credentials not configured
```
**Solución**: Configurar variables de entorno de Azure Storage.

#### Error de Redis
```
Redis client not available
```
**Solución**: Configurar `REDIS_URL` o verificar conectividad a Redis.

### Logs y Debugging

#### Habilitar Logging Detallado
```bash
python scripts/cleanup/orphans_audit.py --verbose
```

#### Verificar Configuración
```python
# En el script
print(f"Azure available: {AZURE_AVAILABLE}")
print(f"Redis available: {REDIS_AVAILABLE}")
print(f"Database configured: {hasattr(settings, 'DATABASES')}")
```

## Documentación Relacionada

- **Plan de Limpieza**: `docs/diagnostico/cleanup_plan.md`
- **Diagnóstico Final**: `docs/diagnostico/diagnostico_final.md`
- **Plan de Remediación**: `docs/diagnostico/plan_remediacion.md`

## Contacto y Soporte

Para problemas o preguntas sobre las herramientas de limpieza:
1. Revisar esta documentación
2. Consultar el plan de limpieza
3. Contactar al equipo de desarrollo

## Changelog

### v1.0.0 (2025-08-12)
- Implementación inicial de auditoría de datos huérfanos
- Soporte para blobs, documentos, contactos, Redis y búsqueda
- Modo dry-run por defecto con confirmación para limpieza real
- Reportes JSON detallados
- Manejo gracioso de servicios no disponibles
- Documentación completa y ejemplos de uso
