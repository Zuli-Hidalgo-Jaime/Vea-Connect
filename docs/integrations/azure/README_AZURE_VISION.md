# Azure Computer Vision Integration - FASE 3

Este documento describe la integración completa de Azure Computer Vision en la aplicación VEA Connect para la extracción de texto desde imágenes y documentos PDF.

## 🎯 Objetivos Completados

✅ **Servicio AzureVisionService creado** con métodos:
- `extract_text_from_image(file_path: str) -> str`
- `extract_text_from_pdf(file_path: str) -> str`

✅ **Configuración de Azure Computer Vision** con:
- `VISION_ENDPOINT`
- `VISION_KEY`

✅ **Validación de extracción de texto** desde imágenes y PDF
✅ **Pruebas manuales y unitarias** incluidas
✅ **Sin emojis ni caracteres especiales** en el texto extraído
✅ **Docstrings en inglés** para todos los métodos, clases y funciones

## 📁 Estructura del Proyecto

```
apps/vision/
├── __init__.py
├── apps.py                          # Configuración de la app Django
├── azure_vision_service.py          # Servicio principal
├── views.py                         # Vistas Django para API
├── urls.py                          # URLs de la aplicación
└── management/
    └── commands/
        └── test_vision_service.py   # Comando de gestión para pruebas

tests/unit/
└── test_azure_vision_service.py     # Pruebas unitarias

scripts/
└── test_azure_vision.py             # Script de prueba manual

docs/
└── azure_vision_integration.md      # Documentación completa
```

## 🚀 Instalación y Configuración

### 1. Dependencias

Las siguientes dependencias se han agregado a `requirements.txt`:

```txt
# Azure Computer Vision
azure-cognitiveservices-vision-computervision==0.9.0
azure-ai-formrecognizer==3.3.0
Pillow==10.0.1
```

### 2. Variables de Entorno

Agregar al archivo `.env`:

```bash
# Azure Computer Vision Configuration
VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com/
VISION_KEY=your-vision-api-key
```

### 3. Configuración de Django

La aplicación `apps.vision` se ha agregado a `INSTALLED_APPS` en `config/settings/base.py`.

## 🔧 Uso del Servicio

### Uso Básico

```python
from apps.vision.azure_vision_service import AzureVisionService

# Inicializar el servicio
vision_service = AzureVisionService()

# Extraer texto de una imagen
texto_imagen = vision_service.extract_text_from_image("ruta/imagen.jpg")

# Extraer texto de un PDF
texto_pdf = vision_service.extract_text_from_pdf("ruta/documento.pdf")

# Verificar disponibilidad del servicio
disponible = vision_service.is_service_available()
```

### Formatos Soportados

**Imágenes:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif)
- TIFF (.tiff, .tif)

**Documentos:**
- PDF (.pdf)

## 🧪 Pruebas

### Pruebas Unitarias

```bash
# Ejecutar todas las pruebas unitarias
python manage.py test tests.unit.test_azure_vision_service

# Ejecutar pruebas específicas
python manage.py test tests.unit.test_azure_vision_service.TestAzureVisionService.test_extract_text_from_image_success
```

### Pruebas Manuales

#### Usando el Script de Prueba

```bash
# Verificar disponibilidad del servicio
python scripts/test_azure_vision.py --test-service

# Probar extracción de texto de imagen
python scripts/test_azure_vision.py --image ruta/imagen.jpg

# Probar extracción de texto de PDF
python scripts/test_azure_vision.py --pdf ruta/documento.pdf

# Crear imagen de prueba
python scripts/test_azure_vision.py --create-test-image
```

#### Usando el Comando de Gestión de Django

```bash
# Verificar servicio
python manage.py test_vision_service --check-service

# Probar imagen
python manage.py test_vision_service --image ruta/imagen.jpg

# Probar PDF
python manage.py test_vision_service --pdf ruta/documento.pdf

# Crear imagen de prueba
python manage.py test_vision_service --create-test-image
```

## 🌐 API Endpoints

La aplicación expone los siguientes endpoints:

- `POST /api/vision/extract-text/` - Extraer texto de archivo subido
- `GET /api/vision/service-status/` - Verificar estado del servicio
- `GET /api/vision/supported-formats/` - Obtener formatos soportados

### Ejemplo de Uso de la API

```bash
# Extraer texto de archivo
curl -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@imagen.jpg" \
  http://localhost:8000/api/vision/extract-text/

# Verificar estado del servicio
curl http://localhost:8000/api/vision/service-status/

# Obtener formatos soportados
curl http://localhost:8000/api/vision/supported-formats/
```

## 🔍 Características del Servicio

### AzureVisionService

**Métodos Principales:**

1. **`__init__()`**
   - Inicializa el servicio con credenciales de Azure
   - Valida la configuración requerida

2. **`extract_text_from_image(file_path: str) -> str`**
   - Extrae texto de imágenes usando OCR
   - Valida formato de archivo
   - Limpia texto extraído

3. **`extract_text_from_pdf(file_path: str) -> str`**
   - Extrae texto de PDFs usando Form Recognizer
   - Procesa múltiples páginas
   - Limpia texto extraído

4. **`_clean_text(text: str) -> str`**
   - Elimina emojis y caracteres especiales
   - Normaliza espacios en blanco
   - Mantiene solo caracteres legibles

5. **`is_service_available() -> bool`**
   - Verifica disponibilidad del servicio
   - Valida credenciales

### Manejo de Errores

El servicio incluye manejo completo de errores:

```python
try:
    texto = vision_service.extract_text_from_image("imagen.jpg")
except FileNotFoundError:
    print("Archivo no encontrado")
except ValueError as e:
    print(f"Formato de archivo inválido: {e}")
except Exception as e:
    print(f"Error de extracción: {e}")
```

## 📊 Pruebas Implementadas

### Pruebas Unitarias

- ✅ Inicialización exitosa del servicio
- ✅ Validación de configuración faltante
- ✅ Extracción de texto de imágenes
- ✅ Extracción de texto de PDFs
- ✅ Manejo de archivos no encontrados
- ✅ Validación de formatos de archivo
- ✅ Limpieza de texto (eliminación de emojis)
- ✅ Verificación de disponibilidad del servicio

### Pruebas de Integración

- ✅ Verificación de credenciales reales
- ✅ Pruebas con archivos reales
- ✅ Validación de respuestas de Azure

## 🔒 Consideraciones de Seguridad

1. **Credenciales**: Las claves API nunca se incluyen en el código
2. **Validación de Archivos**: Se valida tipo y tamaño de archivos
3. **Limpieza de Archivos**: Los archivos temporales se eliminan automáticamente
4. **Manejo de Errores**: No se exponen detalles sensibles en errores

## ⚡ Consideraciones de Rendimiento

1. **Tamaño de Archivo**: Límite de 10MB por archivo
2. **Limpieza Automática**: Archivos temporales se eliminan después del procesamiento
3. **Logging**: Registro detallado para monitoreo
4. **Validación Temprana**: Validación de archivos antes del procesamiento

## 🛠️ Troubleshooting

### Problemas Comunes

1. **Error de Configuración**
   ```bash
   # Verificar variables de entorno
   echo $VISION_ENDPOINT
   echo $VISION_KEY
   ```

2. **Error de Formato de Archivo**
   ```bash
   # Verificar formato soportado
   python manage.py test_vision_service --check-service
   ```

3. **Error de Red**
   ```bash
   # Verificar conectividad
   curl -I $VISION_ENDPOINT
   ```

### Logs de Debug

```python
import logging
logging.getLogger('apps.vision').setLevel(logging.DEBUG)
```

## 📈 Próximas Mejoras

1. **Procesamiento por Lotes**: Procesar múltiples archivos simultáneamente
2. **Detección de Idioma**: Detectar y manejar múltiples idiomas
3. **Análisis de Layout**: Extraer datos estructurados de documentos
4. **Preprocesamiento de Imágenes**: Mejorar precisión OCR
5. **Capa de Caché**: Implementar caché de resultados

## 📝 Documentación Adicional

- [Documentación Completa](docs/azure_vision_integration.md)
- [Ejemplos de Uso](docs/azure_vision_integration.md#usage)
- [Guía de Troubleshooting](docs/azure_vision_integration.md#troubleshooting)

## ✅ Checklist de Validación

- [x] Servicio AzureVisionService creado
- [x] Métodos `extract_text_from_image` y `extract_text_from_pdf` implementados
- [x] Configuración con `VISION_ENDPOINT` y `VISION_KEY`
- [x] Validación de extracción de texto desde imágenes
- [x] Validación de extracción de texto desde PDFs
- [x] Pruebas unitarias completas
- [x] Script de prueba manual
- [x] Comando de gestión de Django
- [x] API endpoints implementados
- [x] Documentación completa
- [x] Sin emojis ni caracteres especiales en texto extraído
- [x] Docstrings en inglés para todos los elementos
- [x] Manejo de errores robusto
- [x] Consideraciones de seguridad implementadas

## 🎉 Conclusión

La integración de Azure Computer Vision ha sido completada exitosamente con todas las funcionalidades requeridas. El servicio está listo para ser utilizado en producción con las credenciales apropiadas de Azure. 