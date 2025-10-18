# Azure Functions - VeaConnect

Este directorio contiene las Azure Functions para el proyecto VeaConnect.

## Funciones Disponibles

### 1. Embedding API Functions (`embedding_api_function_traditional.py`)
- **Ruta**: `/api/embeddings/create` - Crear embeddings
- **Ruta**: `/api/embeddings/search` - Buscar embeddings similares
- **Ruta**: `/api/embeddings/health` - Verificación de salud
- **Ruta**: `/api/embeddings/stats` - Estadísticas

### 2. WhatsApp Event Grid Functions (`whatsapp_event_grid_traditional.py`)
- **Ruta**: `/api/whatsapp/event-grid` - Procesar eventos de WhatsApp
- **Ruta**: `/api/whatsapp/health` - Verificación de salud
- **Ruta**: `/api/whatsapp/test` - Función de prueba
- **Ruta**: `/api/whatsapp/stats` - Estadísticas

### 3. Health Check (`function_app.py`)
- **Ruta**: `/api/health` - Verificación de salud general

## Configuración Local

### Prerrequisitos

1. **Azure Functions Core Tools** (versión 4.x)
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

2. **Python 3.10+**

3. **Azure Storage Emulator** (opcional, para desarrollo local)

### Instalación y Ejecución

#### Opción 1: Usando el script de PowerShell
```powershell
.\start_local.ps1
```

#### Opción 2: Manual
```bash
# 1. Navegar al directorio functions
cd functions

# 2. Crear entorno virtual (si no existe)
python -m venv .venv

# 3. Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Iniciar Azure Functions
func start --port 7072
```

### Variables de Entorno

Configura las siguientes variables en `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "AZURE_OPENAI_ENDPOINT": "tu-endpoint",
    "AZURE_OPENAI_API_KEY": "tu-api-key",
    "AZURE_SEARCH_ENDPOINT": "tu-search-endpoint",
    "AZURE_SEARCH_KEY": "tu-search-key",
    "AZURE_SEARCH_INDEX_NAME": "embeddings-index",
    "ACS_CONNECTION_STRING": "tu-acs-connection-string",
    "ACS_PHONE_NUMBER": "tu-phone-number",
    "ACS_WHATSAPP_API_KEY": "tu-whatsapp-api-key",
    "ACS_WHATSAPP_ENDPOINT": "tu-whatsapp-endpoint"
  }
}
```

## Pruebas

### Health Check
```bash
curl http://localhost:7072/api/health
```

### Embedding API
```bash
# Crear embedding
curl -X POST http://localhost:7072/api/embeddings/create \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "metadata": {"source": "test"}}'

# Buscar embeddings similares
curl -X POST http://localhost:7072/api/embeddings/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "top_k": 5}'
```

### WhatsApp Functions
```bash
# Health check
curl http://localhost:7072/api/whatsapp/health

# Test function
curl -X POST http://localhost:7072/api/whatsapp/test \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

## Despliegue

### Desplegar a Azure
```bash
# Publicar funciones
func azure functionapp publish tu-function-app-name
```

### Crear ZIP para despliegue
```bash
func pack
```

## Solución de Problemas

### Error: "No job functions found"
- Verifica que estés en el directorio `functions/`
- Asegúrate de que `function_app.py` existe y está configurado correctamente
- Verifica que las dependencias estén instaladas

### Error: "Module not found"
- Activa el entorno virtual: `.venv\Scripts\activate`
- Instala las dependencias: `pip install -r requirements.txt`

### Error: "Port already in use"
- Cambia el puerto: `func start --port 7073`
- O termina el proceso que está usando el puerto 7072

## Estructura de Archivos

```
functions/
├── function_app.py                    # Punto de entrada principal
├── embedding_api_function_traditional.py  # Funciones de embeddings
├── whatsapp_event_grid_traditional.py     # Funciones de WhatsApp
├── host.json                          # Configuración de Azure Functions
├── local.settings.json                # Configuración local
├── requirements.txt                   # Dependencias de Python
├── .funcignore                        # Archivos a ignorar
├── start_local.ps1                    # Script de inicio
└── README.md                          # Este archivo
``` 