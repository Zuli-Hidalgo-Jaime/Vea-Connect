---
page_type: sample
languages:
- azdeveloper
- python
- bicep
- html
products:
- azure
- azure-app-service
- azure-database-postgresql
- azure-virtual-network
urlFragment: msdocs-django-postgresql-sample-app
name: Deploy a Python (Django) web app with PostgreSQL in Azure
description: This is a Python web app using the Django framework and the Azure Database for PostgreSQL relational database service. 
---
<!-- YAML front-matter schema: https://review.learn.microsoft.com/en-us/help/contribute/samples/process/onboarding?branch=main#supported-metadata-fields-for-readmemd -->

# VEA WebApp

Aplicación web Django para la gestión de eventos, donaciones, documentos y contactos de la iglesia VEA.

## Configuración de Entornos

### 🏠 Desarrollo Local

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/dfernandezmOnesec/vea-webapp.git
   cd vea-webapp
   ```

2. **Crea un entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En macOS/Linux:
   source venv/bin/activate
   ```

3. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura las variables de entorno:**
   Crea un archivo `.env` en la raíz del proyecto:
   ```env
   # Azure Blob Storage (requerido para desarrollo)
   BLOB_ACCOUNT_NAME=tu_cuenta_blob
   BLOB_ACCOUNT_KEY=tu_clave_blob
   BLOB_CONTAINER_NAME=tu_contenedor
   
   # Azure AI Search (nuevo backend de búsqueda)
   # Este cambio se realizó basado en un análisis de costos y mantenimiento. Azure AI Search ofrece un menor costo operativo y mayor facilidad de gestión frente a Redis Stack para escenarios de búsqueda semántica.
   AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
   AZURE_SEARCH_KEY=your-search-key
   AZURE_SEARCH_INDEX_NAME=documents
   
   # Django (opcional, usa valores por defecto en desarrollo)
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   ```

5. **Aplica las migraciones:**
   ```bash
   python manage.py migrate
   ```

6. **Crea un superusuario:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecuta el servidor:**
   ```bash
   python manage.py runserver
   ```

**Nota:** En desarrollo local, la aplicación usa automáticamente SQLite para la base de datos.

### 🧪 CI/CD (GitHub Actions)

El pipeline de CI/CD está configurado para:
- Usar PostgreSQL local en contenedores
- Ejecutar pruebas unitarias, funcionales e integración
- Verificar la calidad del código con flake8
- Generar reportes de cobertura

Las variables de entorno se configuran automáticamente en el workflow.

### 🚀 Producción (Azure)

Para desplegar en Azure:

1. **Configura Azure Key Vault** con los siguientes secretos:
   - `DB_NAME`: Nombre de la base de datos PostgreSQL
   - `DB_USER`: Usuario de la base de datos
   - `DB_PASSWORD`: Contraseña de la base de datos
   - `DB_HOST`: Host de la base de datos
   - `DB_PORT`: Puerto de la base de datos (5432)
   - `SECRET_KEY`: Clave secreta de Django
   - `BLOB_ACCOUNT_NAME`: Nombre de la cuenta de Azure Blob Storage
   - `BLOB_ACCOUNT_KEY`: Clave de la cuenta de Azure Blob Storage
   - `BLOB_CONTAINER_NAME`: Nombre del contenedor de Azure Blob Storage

2. **Configura las variables de entorno en Azure App Service:**
   - `DJANGO_ENV=production`
   - `DJANGO_SETTINGS_MODULE=config.settings.production`

3. **Despliega usando el workflow de GitHub Actions** o Azure CLI.

## Estructura del Proyecto

```
vea-webapp/
├── apps/                    # Aplicaciones Django
│   ├── core/               # Usuarios y autenticación
│   ├── dashboard/          # Panel principal
│   ├── directory/          # Gestión de contactos
│   ├── documents/          # Gestión de documentos
│   ├── donations/          # Gestión de donaciones
│   ├── events/             # Gestión de eventos
│   └── user_settings/      # Configuración de usuario
├── config/                 # Configuración del proyecto
│   └── settings/           # Configuraciones por entorno
├── static/                 # Archivos estáticos
├── templates/              # Plantillas HTML
├── tests/                  # Pruebas automatizadas
└── requirements.txt        # Dependencias de Python
```

## Características

- ✅ **Autenticación personalizada** con email
- ✅ **Gestión de eventos** con fechas y ubicaciones
- ✅ **Sistema de donaciones** con múltiples tipos y métodos
- ✅ **Directorio de contactos** organizado por ministerios
- ✅ **Gestión de documentos** con categorías
- ✅ **Panel de administración** personalizado
- ✅ **Almacenamiento en Azure Blob Storage**
- ✅ **Búsqueda semántica con Azure AI Search**
- ✅ **Base de datos PostgreSQL** en producción
- ✅ **Pruebas automatizadas** con cobertura
- ✅ **CI/CD** con GitHub Actions

## Tecnologías

- **Backend:** Django 5.2
- **Base de datos:** PostgreSQL (producción), SQLite (desarrollo)
- **Frontend:** Bootstrap 5, FontAwesome
- **Almacenamiento:** Azure Blob Storage
- **Búsqueda:** Azure AI Search
- **Despliegue:** Azure App Service
- **CI/CD:** GitHub Actions
- **Pruebas:** pytest, coverage

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE.md` para más detalles.
