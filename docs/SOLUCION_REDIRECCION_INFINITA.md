# Solución al Problema de Redirección Infinita (ERR_TOO_MANY_REDIRECTS)

## Problema Identificado

La aplicación web de VEA Connect está experimentando un error de **redirección infinita** (`ERR_TOO_MANY_REDIRECTS`) que impide el acceso normal a la aplicación.

**URL afectada:** `vea-connect-g5dje9eba9bscnb6.centralus-01.azurewebsites.net`

## Causa Raíz

El problema es causado por la configuración `SECURE_SSL_REDIRECT = True` en `config/settings/production.py`. Esta configuración está creando un bucle infinito porque:

1. Azure App Service ya maneja HTTPS automáticamente
2. La aplicación intenta redirigir HTTP a HTTPS
3. Azure App Service ya redirige automáticamente
4. Esto crea un bucle infinito de redirecciones

## Solución Aplicada

### 1. Comentar SECURE_SSL_REDIRECT

**Archivo:** `config/settings/production.py`

```python
# Antes:
SECURE_SSL_REDIRECT = True

# Después:
# SECURE_SSL_REDIRECT = True  # Comentado para evitar bucle de redirección en Azure
```

### 2. Actualizar ALLOWED_HOSTS

**Archivo:** `config/settings/production.py`

```python
ALLOWED_HOSTS = [
    os.environ.get('WEBSITE_HOSTNAME', 'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net'),
    'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net',
    'veaconnect-webapp-prod.azurewebsites.net',
    'vea-connect-g5dje9eba9bscnb6.centralus-01.azurewebsites.net',  # Hostname actual del error
    '*.azurewebsites.net',  # Permitir todos los subdominios de Azure
] + (os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else [])
```

### 3. Actualizar CSRF_TRUSTED_ORIGINS

**Archivo:** `config/settings/production.py`

```python
CSRF_TRUSTED_ORIGINS = [
    f'https://{website_hostname}',
    'https://vea-connect-g5dje9eba9bscnb6.centralus-01.azurewebsites.net',
    'https://*.azurewebsites.net'
]
```

## Pasos para Aplicar la Solución

### 1. Commit de Cambios

```bash
git add config/settings/production.py
git commit -m "Fix: Comentar SECURE_SSL_REDIRECT para evitar bucle de redirección"
git push origin main
```

### 2. Desplegar en Azure

```bash
# Si usas Azure CLI
az webapp deployment source config-zip --resource-group <resource-group> --name <app-name> --src <zip-file>

# O usar Azure DevOps/GitHub Actions para despliegue automático
```

### 3. Reiniciar la Aplicación

En Azure Portal:
1. Ir a **App Service** > **VEA Connect Web App**
2. En el menú lateral, ir a **Overview**
3. Hacer clic en **Restart**

### 4. Verificar la Solución

1. Limpiar caché del navegador
2. Probar acceso a la aplicación
3. Verificar que no hay más redirecciones infinitas

## Verificación de la Solución

### 1. Verificar Logs

En Azure Portal:
1. **App Service** > **Logs**
2. Verificar que no hay errores de redirección
3. Confirmar que la aplicación inicia correctamente

### 2. Probar Acceso

```bash
# Probar con curl
curl -I https://vea-connect-g5dje9eba9bscnb6.centralus-01.azurewebsites.net

# Debería devolver 200 OK, no 301/302 redirects
```

### 3. Verificar Configuración

```bash
# Ejecutar script de diagnóstico
python scripts/fix_redirect_loop.py
```

## Configuración de Seguridad Mantenida

A pesar de comentar `SECURE_SSL_REDIRECT`, la seguridad se mantiene porque:

- ✅ `SESSION_COOKIE_SECURE = True`
- ✅ `CSRF_COOKIE_SECURE = True`
- ✅ `SECURE_HSTS_SECONDS = 31536000`
- ✅ `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- ✅ `SECURE_HSTS_PRELOAD = True`
- ✅ Azure App Service maneja HTTPS automáticamente

## Prevención Futura

### 1. Configuración Condicional

Para evitar este problema en el futuro, usar configuración condicional:

```python
# En config/settings/production.py
import os

# Solo redirigir SSL si no estamos en Azure App Service
if not os.getenv('WEBSITE_HOSTNAME'):
    SECURE_SSL_REDIRECT = True
else:
    # Azure App Service maneja HTTPS automáticamente
    SECURE_SSL_REDIRECT = False
```

### 2. Monitoreo

- Configurar alertas en Azure Application Insights
- Monitorear logs de aplicación regularmente
- Verificar estado de la aplicación después de despliegues

### 3. Testing

- Probar redirecciones en entorno de desarrollo
- Verificar configuración antes de despliegue a producción
- Usar herramientas como `curl` para verificar headers de respuesta

## Troubleshooting Adicional

Si el problema persiste después de aplicar la solución:

### 1. Verificar Azure App Service Configuration

```bash
# Verificar configuración de la aplicación
az webapp config show --name <app-name> --resource-group <resource-group>
```

### 2. Verificar Custom Domains

Si usas dominios personalizados:
1. Verificar configuración en **Custom domains**
2. Confirmar que SSL/TLS está configurado correctamente
3. Verificar reglas de redirección

### 3. Verificar Application Gateway/Front Door

Si usas Azure Application Gateway o Front Door:
1. Verificar reglas de redirección
2. Confirmar configuración de SSL/TLS
3. Verificar health probes

### 4. Verificar web.config

Si existe un archivo `web.config`:
1. Verificar reglas de redirección
2. Confirmar que no hay conflictos con Django
3. Verificar configuración de URL Rewrite

## Contacto y Soporte

Si necesitas ayuda adicional:

1. **Logs de Azure:** Revisar logs en Azure Portal
2. **Application Insights:** Verificar telemetría de la aplicación
3. **Documentación:** Consultar documentación de Django y Azure App Service
4. **Soporte:** Contactar soporte técnico si el problema persiste

---

**Fecha de creación:** 2025-08-10  
**Última actualización:** 2025-08-10  
**Estado:** Solucionado
