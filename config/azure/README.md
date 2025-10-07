# VEA Connect - Configuración de Azure

Esta carpeta contiene los archivos de configuración necesarios para desplegar y configurar VEA Connect en Azure.

## Archivos de Configuración

### 1. `vea-connect-index.json`
Define el índice de búsqueda de Azure AI Search con los siguientes campos:
- **Campos básicos**: content, metadata_storage_name, metadata_storage_path
- **Campos de metadatos**: metadata_storage_size, metadata_storage_last_modified
- **Campos de IA**: locations, keyphrases, language, merged_content
- **Campos de OCR**: text, layoutText, imageTags, imageCaption
- **Campos personalizados**: document_type, category, confidence_score

### 2. `vea-connect-skillset.json`
Define las habilidades de IA que se aplicarán a los documentos:
- **OCR**: Extracción de texto de imágenes
- **Análisis de Entidades**: Personas, organizaciones, ubicaciones, fechas
- **Extracción de Frases Clave**: Conceptos importantes
- **Detección de Idioma**: Soporte para español
- **Análisis de Imágenes**: Etiquetas y descripciones
- **Categorización**: Clasificación automática de documentos

### 3. `vea-connect-indexer.json`
Configura el indexer que conecta Azure Blob Storage con Azure AI Search:
- **Fuente de datos**: Azure Blob Storage
- **Procesamiento**: Aplicación de habilidades de IA
- **Mapeo de campos**: Asignación de campos de entrada y salida

### 4. `vea-connect-datasource.json`
Define la fuente de datos de Azure Blob Storage:
- **Tipo**: Azure Blob Storage
- **Contenedor**: admin-documentos
- **Conexión**: Cadena de conexión de Azure Storage

## Scripts de Despliegue

### 1. `deploy-azure-resources.ps1`
Script de PowerShell para crear los recursos básicos de Azure:
- Grupo de recursos
- Azure AI Search
- Azure Storage Account
- Azure Cognitive Services
- Contenedor de blob storage

**Uso:**
```powershell
.\deploy-azure-resources.ps1 -ResourceGroupName "vea-connect-rg" -Location "East US" -SearchServiceName "vea-connect-search" -StorageAccountName "veaconnectstorage" -CognitiveServicesName "vea-connect-cognitive"
```

### 2. `setup-search-resources.ps1`
Script de PowerShell para configurar Azure AI Search:
- Crear data source
- Crear skillset
- Crear índice
- Crear indexer
- Ejecutar indexer

**Uso:**
```powershell
.\setup-search-resources.ps1 -SearchServiceName "vea-connect-search" -SearchServiceKey "tu-clave" -StorageConnectionString "tu-cadena-conexion" -CognitiveServicesKey "tu-clave-cognitiva"
```

## Proceso de Despliegue

### Paso 1: Crear Recursos de Azure
```powershell
# Ejecutar el script de despliegue
.\deploy-azure-resources.ps1 -ResourceGroupName "vea-connect-rg" -Location "East US" -SearchServiceName "vea-connect-search" -StorageAccountName "veaconnectstorage" -CognitiveServicesName "vea-connect-cognitive"
```

### Paso 2: Configurar Azure AI Search
```powershell
# Ejecutar el script de configuración
.\setup-search-resources.ps1 -SearchServiceName "vea-connect-search" -SearchServiceKey "tu-clave" -StorageConnectionString "tu-cadena-conexion" -CognitiveServicesKey "tu-clave-cognitiva"
```

### Paso 3: Subir Documentos
1. Subir documentos al contenedor `admin-documentos` en Azure Storage
2. El indexer procesará automáticamente los documentos
3. Los documentos estarán disponibles para búsqueda

### Paso 4: Verificar Configuración
1. Ir al portal de Azure
2. Navegar a Azure AI Search
3. Verificar que el indexer se ejecutó correctamente
4. Probar búsquedas en el índice

## Configuración de Variables de Entorno

Después de ejecutar los scripts, se generará un archivo `env_example.txt` con las variables de entorno necesarias:

```env
# Azure AI Search
SEARCH_SERVICE_NAME=vea-connect-search
SEARCH_SERVICE_ENDPOINT=https://vea-connect-search.search.windows.net
SEARCH_SERVICE_KEY=tu-clave
SEARCH_INDEX_NAME=vea-connect-index

# Azure Storage
STORAGE_ACCOUNT_NAME=veaconnectstorage
STORAGE_CONTAINER_NAME=admin-documentos
STORAGE_CONNECTION_STRING=tu-cadena-conexion

# Azure Cognitive Services
COGNITIVE_SERVICES_KEY=tu-clave-cognitiva
COGNITIVE_SERVICES_ENDPOINT=https://vea-connect-cognitive.cognitiveservices.azure.com/
```

## Próximos Pasos

1. **Configurar Backend**: Usar las variables de entorno en el backend de Python
2. **Implementar Búsqueda**: Crear el cliente de Azure AI Search
3. **Desarrollar Frontend**: Crear la interfaz de búsqueda
4. **Probar Sistema**: Subir documentos y probar búsquedas

## Notas Importantes

- **Idioma**: Los archivos están configurados para español (es.microsoft analyzer)
- **OCR**: Habilitado para extraer texto de imágenes
- **Categorización**: Los documentos se categorizan automáticamente
- **Escalabilidad**: La configuración soporta crecimiento del sistema




