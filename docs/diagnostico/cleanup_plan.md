# Plan de Limpieza de Datos Huérfanos

## Resumen Ejecutivo

Este documento describe el proceso de limpieza de datos huérfanos en el sistema VeaConnect, incluyendo los pasos de verificación manual que deben realizarse antes de ejecutar cualquier operación de eliminación.

## Datos Auditados

### 1. Blobs Huérfanos (Azure Storage)
- **Descripción**: Archivos en Azure Blob Storage que no tienen referencia en la base de datos
- **Criterios**: Blobs más antiguos de 30 días sin registro correspondiente en `Document`
- **Riesgo**: Bajo (solo archivos no referenciados)

### 2. Documentos Huérfanos (Base de Datos)
- **Descripción**: Registros en la tabla `Document` que referencian blobs inexistentes
- **Criterios**: Documentos que apuntan a blobs que ya no existen en Azure Storage
- **Riesgo**: Medio (pueden causar errores 404)

### 3. Contactos Huérfanos (Base de Datos)
- **Descripción**: Contactos muy antiguos sin actividad reciente
- **Criterios**: Contactos creados hace más de 30 días sin actualizaciones recientes
- **Riesgo**: Bajo (datos históricos inactivos)

### 4. Claves Redis Huérfanas (Cache)
- **Descripción**: Claves de cache sin TTL configurado
- **Criterios**: Claves con patrones específicos (`vea:emb:*`, `vea:ans:*`, etc.) sin expiración
- **Riesgo**: Bajo (solo afecta rendimiento de cache)

### 5. Documentos de Búsqueda Huérfanos (Azure AI Search)
- **Descripción**: Documentos en el índice de búsqueda sin correspondencia en la base de datos
- **Criterios**: Pendiente de implementación
- **Riesgo**: Bajo (solo afecta resultados de búsqueda)

## Proceso de Verificación Manual

### Paso 1: Ejecutar Auditoría en Modo Dry-Run

```bash
# Ejecutar auditoría completa
python scripts/cleanup/orphans_audit.py --verbose

# Ejecutar con umbral personalizado (ej: 60 días)
python scripts/cleanup/orphans_audit.py --days 60 --verbose

# Exportar reporte con nombre personalizado
python scripts/cleanup/orphans_audit.py --output logs/audit_manual_review.json
```

### Paso 2: Revisar el Reporte Generado

1. **Ubicación del reporte**: `logs/cleanup_report_YYYYMMDD_HHMMSS.json`
2. **Contenido a revisar**:
   - Resumen de elementos huérfanos encontrados
   - Detalles específicos de cada elemento
   - Razones por las que se consideran huérfanos

### Paso 3: Verificación Manual por Tipo de Dato

#### 3.1 Blobs Huérfanos

**Verificación en Azure Portal**:
1. Ir a Azure Portal → Storage Account → Containers
2. Navegar al contenedor de documentos
3. Verificar manualmente los blobs listados como huérfanos
4. Confirmar que no son necesarios para el funcionamiento del sistema

**Verificación en Base de Datos**:
```sql
-- Verificar si hay referencias a blobs huérfanos
SELECT id, title, file_path, created_at 
FROM documents_document 
WHERE file_path IN ('blob_name_1', 'blob_name_2', ...);
```

#### 3.2 Documentos Huérfanos

**Verificación en Base de Datos**:
```sql
-- Verificar documentos que podrían estar huérfanos
SELECT id, title, file_path, created_at, updated_at
FROM documents_document 
WHERE created_at < '2024-01-01'  -- Ajustar fecha según umbral
ORDER BY created_at DESC;
```

**Verificación de Integridad**:
1. Intentar acceder a los documentos desde la aplicación
2. Verificar si generan errores 404
3. Confirmar que no son referenciados por otros módulos

#### 3.3 Contactos Huérfanos

**Verificación de Relaciones**:
```sql
-- Verificar si los contactos tienen documentos asociados
SELECT c.id, c.name, c.email, COUNT(d.id) as doc_count
FROM directory_contact c
LEFT JOIN documents_document d ON c.id = d.contact_id
WHERE c.created_at < '2024-01-01'  -- Ajustar fecha según umbral
GROUP BY c.id, c.name, c.email
HAVING COUNT(d.id) = 0;
```

**Verificación de Actividad**:
1. Revisar logs de actividad para estos contactos
2. Verificar si han tenido interacciones recientes
3. Confirmar que no son contactos importantes históricamente

#### 3.4 Claves Redis Huérfanas

**Verificación en Redis**:
```bash
# Conectar a Redis y verificar claves
redis-cli -h <host> -p <port> -a <password>

# Listar claves con patrones específicos
KEYS vea:emb:*
KEYS vea:ans:*
KEYS vea:sas:*

# Verificar TTL de claves específicas
TTL vea:emb:example_key
```

**Verificación de Uso**:
1. Verificar si las claves son accedidas por la aplicación
2. Confirmar que no son necesarias para el funcionamiento
3. Revisar logs de cache para patrones de uso

### Paso 4: Análisis de Impacto

#### 4.1 Evaluación de Riesgo

**Riesgo Bajo** (Puede proceder con limpieza):
- Blobs sin referencia en BD
- Claves Redis sin TTL
- Contactos muy antiguos sin actividad

**Riesgo Medio** (Requiere verificación adicional):
- Documentos que referencian blobs inexistentes
- Contactos con documentos asociados

**Riesgo Alto** (No limpiar sin revisión exhaustiva):
- Datos de producción activos
- Información crítica del negocio
- Datos de auditoría requeridos

#### 4.2 Estimación de Espacio Liberado

```bash
# Calcular tamaño total de blobs huérfanos
python -c "
import json
with open('logs/cleanup_report_YYYYMMDD_HHMMSS.json') as f:
    data = json.load(f)
    
total_size = sum(blob['size'] for blob in data['details']['orphaned_blobs'])
print(f'Espacio a liberar: {total_size / (1024*1024):.2f} MB')
"
```

### Paso 5: Backup y Preparación

#### 5.1 Backup de Datos Críticos

```bash
# Backup de base de datos (ejemplo para PostgreSQL)
pg_dump -h <host> -U <user> -d <database> > backup_before_cleanup.sql

# Backup de configuración
cp config/settings/local.py config/settings/local_backup_$(date +%Y%m%d).py
```

#### 5.2 Preparación del Entorno

1. **Horario de Mantenimiento**: Programar durante ventana de mantenimiento
2. **Notificación**: Informar a usuarios sobre mantenimiento programado
3. **Rollback Plan**: Preparar scripts de rollback si es necesario

## Proceso de Limpieza

### Ejecución de Limpieza

```bash
# Ejecutar limpieza con confirmación
python scripts/cleanup/orphans_audit.py --force

# Ejecutar con umbral personalizado
python scripts/cleanup/orphans_audit.py --force --days 60

# Ejecutar con reporte personalizado
python scripts/cleanup/orphans_audit.py --force --output logs/cleanup_executed.json
```

### Monitoreo Durante la Limpieza

1. **Logs de Aplicación**: Monitorear logs para errores
2. **Métricas de Sistema**: Verificar uso de recursos
3. **Funcionalidad**: Probar funcionalidades críticas

### Verificación Post-Limpieza

#### Verificación Inmediata

```bash
# Ejecutar auditoría post-limpieza
python scripts/cleanup/orphans_audit.py --verbose

# Verificar que no hay elementos huérfanos restantes
python scripts/cleanup/orphans_audit.py --days 1
```

#### Verificación de Funcionalidad

1. **Pruebas de Usuario**: Verificar flujos principales
2. **Pruebas de Documentos**: Subir y descargar documentos
3. **Pruebas de Búsqueda**: Verificar funcionalidad de búsqueda
4. **Pruebas de Cache**: Verificar funcionamiento del cache

## Plan de Rollback

### Rollback Automático

Si se detectan problemas durante la limpieza:

1. **Detener el proceso**: `Ctrl+C` en el script
2. **Verificar estado**: Ejecutar auditoría inmediata
3. **Restaurar si es necesario**: Usar backups creados

### Rollback Manual

```bash
# Restaurar base de datos si es necesario
psql -h <host> -U <user> -d <database> < backup_before_cleanup.sql

# Restaurar configuración
cp config/settings/local_backup_YYYYMMDD.py config/settings/local.py
```

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

# Agregar a crontab (ejecutar semanalmente)
# 0 2 * * 0 /path/to/veaconnect-webapp-prod/scripts/cleanup/scheduled_audit.sh
```

### Alertas y Notificaciones

1. **Alertas de Espacio**: Monitorear uso de Azure Storage
2. **Alertas de Base de Datos**: Monitorear tamaño de tablas
3. **Alertas de Cache**: Monitorear uso de Redis

## Consideraciones Especiales

### Datos de Auditoría

- **Retención Legal**: Verificar requisitos de retención de datos
- **Compliance**: Asegurar cumplimiento con regulaciones
- **Backup**: Mantener backups de datos eliminados si es requerido

### Datos de Producción

- **Horarios**: Ejecutar durante ventanas de bajo tráfico
- **Notificación**: Informar a usuarios sobre mantenimiento
- **Monitoreo**: Supervisar métricas durante y después del proceso

### Datos de Desarrollo/Testing

- **Entornos Separados**: Verificar que se está en el entorno correcto
- **Datos de Prueba**: Preservar datos necesarios para testing
- **Configuración**: Verificar configuración de entorno

## Checklist de Verificación

### Antes de la Limpieza

- [ ] Ejecutar auditoría en modo dry-run
- [ ] Revisar reporte completo
- [ ] Verificar manualmente elementos críticos
- [ ] Crear backup de datos importantes
- [ ] Notificar a usuarios sobre mantenimiento
- [ ] Preparar plan de rollback
- [ ] Verificar configuración de entorno

### Durante la Limpieza

- [ ] Monitorear logs de aplicación
- [ ] Verificar métricas de sistema
- [ ] Probar funcionalidades críticas
- [ ] Documentar cualquier problema

### Después de la Limpieza

- [ ] Ejecutar auditoría post-limpieza
- [ ] Verificar funcionalidad completa
- [ ] Documentar resultados
- [ ] Actualizar métricas de espacio liberado
- [ ] Programar próxima auditoría

## Contactos y Escalación

### Contactos Técnicos

- **Desarrollador Principal**: [Nombre] - [Email]
- **DevOps**: [Nombre] - [Email]
- **DBA**: [Nombre] - [Email]

### Escalación

1. **Problemas Menores**: Resolver según documentación
2. **Problemas Moderados**: Contactar desarrollador principal
3. **Problemas Críticos**: Escalar a equipo completo + rollback inmediato

## Documentación y Registro

### Registro de Limpiezas

Mantener un registro de todas las limpiezas ejecutadas:

```json
{
  "fecha": "2024-01-15T10:00:00Z",
  "ejecutor": "usuario@empresa.com",
  "entorno": "produccion",
  "elementos_eliminados": {
    "blobs": 150,
    "documentos": 25,
    "contactos": 10,
    "redis_keys": 500
  },
  "espacio_liberado_mb": 1024,
  "problemas_encontrados": [],
  "observaciones": "Limpieza exitosa sin incidentes"
}
```

### Actualización de Documentación

- Actualizar este plan según lecciones aprendidas
- Documentar nuevos patrones de datos huérfanos
- Actualizar procedimientos según cambios en el sistema
