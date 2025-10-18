# VeaConnect Coding Standards

## Resumen Ejecutivo

Este documento establece los estándares de código para el proyecto VeaConnect, enfocándose en consistencia, legibilidad y mantenibilidad sin alterar el comportamiento funcional existente.

## Principios Fundamentales

### 1. No Breaking Changes
- **Sin alteraciones funcionales**: Los estándares de estilo no deben cambiar el comportamiento del código
- **Implementación gradual**: Aplicar estándares solo en código nuevo o refactoring planificado
- **Flags de control**: Nuevas funcionalidades detrás de feature flags

### 2. Consistencia
- **Un solo estilo**: Aplicar el mismo estándar en todo el proyecto
- **Documentación clara**: Guías específicas para cada aspecto del código
- **Herramientas automatizadas**: Usar linters y formatters para mantener consistencia

### 3. Profesionalismo
- **Sin emojis**: Código, logs y UI deben ser profesionales
- **Mensajes claros**: Comunicación clara y directa
- **Documentación completa**: Docstrings y comentarios informativos
- **Saneamiento de logs**: Protección de información sensible en logs

## Docstrings

### Estilo Google (Recomendado)

#### Función Simple
```python
def calculate_total_price(items: List[Dict], tax_rate: float) -> float:
    """Calculate the total price including tax for a list of items.
    
    Args:
        items: List of dictionaries containing item information.
            Each dict should have 'price' and 'quantity' keys.
        tax_rate: Tax rate as a decimal (e.g., 0.08 for 8%).
    
    Returns:
        Total price including tax.
    
    Raises:
        ValueError: If tax_rate is negative or items list is empty.
        KeyError: If items don't have required 'price' or 'quantity' keys.
    
    Example:
        >>> items = [{'price': 10.0, 'quantity': 2}, {'price': 5.0, 'quantity': 1}]
        >>> calculate_total_price(items, 0.08)
        27.0
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    return subtotal * (1 + tax_rate)
```

#### Clase
```python
class DocumentProcessor:
    """Process and analyze documents for text extraction and indexing.
    
    This class provides functionality to process various document formats,
    extract text content, and prepare documents for search indexing.
    
    Attributes:
        supported_formats: List of supported file formats.
        max_file_size: Maximum file size in bytes for processing.
        extraction_timeout: Timeout in seconds for text extraction.
    
    Example:
        >>> processor = DocumentProcessor(max_file_size=10*1024*1024)
        >>> result = processor.process_document("document.pdf")
        >>> print(result.text_content[:100])
        'This is the beginning of the extracted text...'
    """
    
    def __init__(self, max_file_size: int = 50 * 1024 * 1024, 
                 extraction_timeout: int = 300):
        """Initialize the DocumentProcessor.
        
        Args:
            max_file_size: Maximum file size in bytes. Defaults to 50MB.
            extraction_timeout: Timeout in seconds for text extraction. 
                Defaults to 300 seconds.
        """
        self.supported_formats = ['.pdf', '.docx', '.txt', '.md']
        self.max_file_size = max_file_size
        self.extraction_timeout = extraction_timeout
    
    def process_document(self, file_path: str) -> DocumentResult:
        """Process a single document and extract its content.
        
        Args:
            file_path: Path to the document file.
        
        Returns:
            DocumentResult containing extracted text and metadata.
        
        Raises:
            FileNotFoundError: If the document file doesn't exist.
            UnsupportedFormatError: If the file format is not supported.
            FileTooLargeError: If the file exceeds max_file_size.
        """
        # Implementation here
        pass
```

#### Módulo
```python
"""
Document processing utilities for VeaConnect.

This module provides tools for processing various document formats,
extracting text content, and preparing documents for search indexing.
It supports PDF, DOCX, TXT, and Markdown formats.

Example:
    >>> from document_utils import DocumentProcessor
    >>> processor = DocumentProcessor()
    >>> result = processor.process_document("sample.pdf")
    >>> print(f"Extracted {len(result.text_content)} characters")

Classes:
    DocumentProcessor: Main class for document processing.
    DocumentResult: Result container for processed documents.
    UnsupportedFormatError: Exception for unsupported file formats.

Functions:
    validate_file_format: Check if a file format is supported.
    extract_metadata: Extract metadata from document files.
"""

# Module implementation...
```

### Estilo NumPy (Alternativo)

```python
def calculate_embeddings(text: str, model_name: str = "text-embedding-ada-002") -> List[float]:
    """Calculate text embeddings using OpenAI's embedding model.
    
    Parameters
    ----------
    text : str
        The input text to embed.
    model_name : str, optional
        The embedding model to use, by default "text-embedding-ada-002"
    
    Returns
    -------
    List[float]
        The embedding vector as a list of floats.
    
    Raises
    ------
    ValueError
        If text is empty or None.
    OpenAIError
        If the API call fails.
    
    Notes
    -----
    This function requires a valid OpenAI API key to be configured.
    The embedding vector will have 1536 dimensions for the default model.
    
    Examples
    --------
    >>> text = "Hello, world!"
    >>> embedding = calculate_embeddings(text)
    >>> len(embedding)
    1536
    >>> all(isinstance(x, float) for x in embedding)
    True
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty or None")
    
    # Implementation here
    pass
```

### Reglas para Docstrings

#### 1. Idioma
- **Siempre en inglés**: Todos los docstrings deben estar en inglés
- **Términos técnicos consistentes**: Usar la misma terminología en todo el proyecto
- **Evitar jerga local**: Usar términos estándar de la industria

#### 2. Estructura
- **Descripción breve**: Primera línea debe ser un resumen conciso
- **Línea en blanco**: Separar descripción de detalles
- **Secciones completas**: Incluir Args, Returns, Raises cuando sea relevante
- **Ejemplos**: Proporcionar ejemplos de uso cuando sea útil

#### 3. Contenido
- **Qué hace**: Explicar claramente qué hace la función/clase
- **Parámetros**: Documentar tipo, propósito y restricciones
- **Retorno**: Describir el valor de retorno y su tipo
- **Excepciones**: Listar todas las excepciones que pueden ser lanzadas
- **Ejemplos**: Incluir ejemplos prácticos de uso

## Prohibición de Emojis

### Regla General
**NO usar emojis en código, logs, o interfaz de usuario.**

### Reemplazos Recomendados

#### En Código
```python
# ❌ INCORRECTO
def process_data():
    """🚀 Process the data and return results! 🎉"""
    logger.info("✅ Data processed successfully!")
    return "🎯 Results ready!"

# ✅ CORRECTO
def process_data():
    """Process the data and return results."""
    logger.info("Data processed successfully")
    return "Results ready"
```

#### En Logs
```python
# ❌ INCORRECTO
logger.info("🚀 Starting application...")
logger.warning("⚠️  High memory usage detected!")
logger.error("💥 Critical error occurred!")

# ✅ CORRECTO
logger.info("Starting application")
logger.warning("High memory usage detected")
logger.error("Critical error occurred")
```

#### En Mensajes de Usuario
```python
# ❌ INCORRECTO
messages.success(request, "✅ File uploaded successfully!")
messages.error(request, "❌ Upload failed!")

# ✅ CORRECTO
messages.success(request, "File uploaded successfully")
messages.error(request, "Upload failed")
```

#### En Comentarios
```python
# ❌ INCORRECTO
# 🚀 This is a critical function
# ⚠️  TODO: Fix this bug
# 💡 Idea: Add caching here

# ✅ CORRECTO
# This is a critical function
# TODO: Fix this bug
# IDEA: Add caching here
```

### Excepciones
- **Documentación externa**: Emojis pueden usarse en README, documentación de usuario, etc.
- **Comunicación informal**: Slack, emails, etc. pueden usar emojis
- **Marketing**: Material promocional puede usar emojis

## Estándares de Logging

### Niveles de Logging

#### DEBUG
```python
logger.debug("Processing user request", extra={
    'user_id': user.id,
    'request_id': request_id,
    'endpoint': request.path
})
```

#### INFO
```python
logger.info("User authentication successful", extra={
    'user_id': user.id,
    'method': 'oauth2'
})
```

#### WARNING
```python
logger.warning("High memory usage detected", extra={
    'memory_usage': memory_usage,
    'threshold': threshold,
    'service': 'document_processor'
})
```

#### ERROR
```python
logger.error("Database connection failed", extra={
    'database': 'postgresql',
    'error_code': error.code,
    'retry_attempt': retry_count
}, exc_info=True)
```

#### CRITICAL
```python
logger.critical("Application startup failed", extra={
    'component': 'database',
    'error': str(error)
}, exc_info=True)
```

### Formato de Mensajes

#### Estructura
```python
# Formato: [Context] Action result/status
logger.info("User authentication successful")
logger.warning("High memory usage detected")
logger.error("Database connection failed")
```

#### Con Contexto
```python
# Formato: [Component] Action result/status
logger.info("[Auth] User login successful")
logger.warning("[Memory] Usage above threshold")
logger.error("[Database] Connection timeout")
```

#### Con Métricas
```python
# Formato: Action result/status (metric: value)
logger.info("Document processed successfully (size: 2.5MB)")
logger.warning("API response slow (latency: 1500ms)")
logger.error("Cache miss (key: user:123:profile)")
```

### Variables de Entorno
```python
# Usar variables de entorno para configuración
import os

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

## Herramientas de Linting y Formateo

### pyproject.toml Sugerido

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "veaconnect-webapp"
version = "1.0.0"
description = "VeaConnect Web Application"
authors = [{name = "VeaConnect Team", email = "team@veaconnect.com"}]
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "django>=4.2",
    "redis>=4.0",
    "azure-storage-blob>=12.0",
    "openai>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-django>=4.5",
    "black>=23.0",
    "ruff>=0.1.0",
    "isort>=5.12",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["apps", "config", "utils"]
known_third_party = ["django", "redis", "azure", "openai"]

[tool.ruff]
target-version = "py39"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*" = ["B011"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "django.*",
    "azure.*",
    "redis.*",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["tests.py", "test_*.py", "*_tests.py"]
addopts = "-v --tb=short"
testpaths = ["tests", "apps"]
```

### Configuración de pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-redis]
        args: [--ignore-missing-imports]

  - repo: local
    hooks:
      - id: django-check
        name: Django check
        entry: python manage.py check
        language: system
        pass_filenames: false
        always_run: true
```

## Parches Sugeridos

### Parche de Configuración de Linting

```diff
# parches_sugeridos/04_style_linting.patch
diff --git a/pyproject.toml b/pyproject.toml
new file mode 100644
index 0000000..a1b2c3d
--- /dev/null
+++ b/pyproject.toml
@@ -0,0 +1,150 @@
+[build-system]
+requires = ["setuptools>=61.0", "wheel"]
+build-backend = "setuptools.build_meta"
+
+[project]
+name = "veaconnect-webapp"
+version = "1.0.0"
+description = "VeaConnect Web Application"
+authors = [{name = "VeaConnect Team", email = "team@veaconnect.com"}]
+readme = "README.md"
+requires-python = ">=3.9"
+
+[tool.black]
+line-length = 88
+target-version = ['py39']
+
+[tool.isort]
+profile = "black"
+line-length = 88
+
+[tool.ruff]
+target-version = "py39"
+line-length = 88
+select = ["E", "W", "F", "I", "B", "C4", "UP"]
+ignore = ["E501", "B008", "C901"]
+
+[tool.mypy]
+python_version = "3.9"
+warn_return_any = true
+disallow_untyped_defs = true
+
+[[tool.mypy.overrides]]
+module = ["django.*", "azure.*", "redis.*"]
+ignore_missing_imports = true
+
diff --git a/.pre-commit-config.yaml b/.pre-commit-config.yaml
new file mode 100644
index 0000000..d4e5f6g
--- /dev/null
+++ b/.pre-commit-config.yaml
@@ -0,0 +1,45 @@
+repos:
+  - repo: https://github.com/pre-commit/pre-commit-hooks
+    rev: v4.4.0
+    hooks:
+      - id: trailing-whitespace
+      - id: end-of-file-fixer
+      - id: check-yaml
+      - id: check-added-large-files
+      - id: check-merge-conflict
+      - id: debug-statements
+
+  - repo: https://github.com/psf/black
+    rev: 23.3.0
+    hooks:
+      - id: black
+        language_version: python3.9
+
+  - repo: https://github.com/pycqa/isort
+    rev: 5.12.0
+    hooks:
+      - id: isort
+        args: ["--profile", "black"]
+
+  - repo: https://github.com/charliermarsh/ruff-pre-commit
+    rev: v0.1.0
+    hooks:
+      - id: ruff
+        args: [--fix, --exit-non-zero-on-fix]
+
+  - repo: https://github.com/pre-commit/mirrors-mypy
+    rev: v1.3.0
+    hooks:
+      - id: mypy
+        additional_dependencies: [types-requests, types-redis]
+        args: [--ignore-missing-imports]
+
+  - repo: local
+    hooks:
+      - id: django-check
+        name: Django check
+        entry: python manage.py check
+        language: system
+        pass_filenames: false
+        always_run: true
```

## Implementación Gradual

### Fase 1: Documentación (Completada)
- ✅ Establecer estándares en este documento
- ✅ Crear parches sugeridos
- ✅ Documentar herramientas recomendadas

### Fase 2: Herramientas (Opcional)
- 🔄 Instalar herramientas de linting
- 🔄 Configurar pre-commit hooks
- 🔄 Integrar con CI/CD

### Fase 3: Aplicación (Futuro)
- 🔄 Aplicar estándares en código nuevo
- 🔄 Refactoring gradual de código existente
- 🔄 Revisión de código con nuevos estándares

## Checklist de Implementación

### Para Nuevo Código
- [ ] Docstrings en inglés (estilo Google o NumPy)
- [ ] Sin emojis en código, logs o UI
- [ ] Mensajes de logging profesionales
- [ ] Saneamiento de información sensible en logs
- [ ] Formateo con black/isort
- [ ] Linting con ruff

### Para Código Existente
- [ ] Revisar y actualizar docstrings gradualmente
- [ ] Reemplazar emojis por texto descriptivo
- [ ] Mejorar mensajes de logging
- [ ] Aplicar formateo cuando se modifique

### Para el Proyecto
- [ ] Configurar herramientas de linting
- [ ] Establecer pre-commit hooks
- [ ] Integrar con pipeline de CI/CD
- [ ] Documentar proceso de revisión de código

## Recursos Adicionales

### Documentación
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://beta.ruff.rs/)

### Herramientas
- [pre-commit](https://pre-commit.com/)
- [mypy](https://mypy.readthedocs.io/)
- [isort](https://pycqa.github.io/isort/)

### Ejemplos
- Ver `docs/estilo/examples/` para ejemplos prácticos
- Ver `parches_sugeridos/04_style_linting.patch` para configuración

## Saneamiento de Logs y Protección de PII

### Principios Fundamentales

#### 1. Protección de Información Sensible
- **Nunca loggear secretos**: API keys, passwords, tokens, connection strings
- **Redactar PII**: Emails, teléfonos, direcciones, nombres completos
- **Sanitizar URLs**: Remover parámetros sensibles de URLs
- **Proteger IPs privadas**: No exponer IPs internas de la infraestructura

#### 2. Uso del Utilitario de Saneamiento
```python
from utils.logging_extras import safe_value, get_safe_logger

# Para valores individuales
logger.info(f"Processing user: {safe_value(user_email)}")
logger.info(f"API response: {safe_value(api_key)}")  # Se convierte en [REDACTED]

# Para loggers seguros
safe_logger = get_safe_logger(__name__)
safe_logger.info("User data: %s", user_data)  # Sanitiza automáticamente
```

#### 3. Patrones de Detección Automática
El utilitario detecta automáticamente:
- **API Keys**: `sk-`, `pk_`, tokens largos alfanuméricos
- **Connection Strings**: Azure, PostgreSQL, Redis
- **URLs con tokens**: Parámetros `token`, `key`, `secret`
- **Emails**: Patrones de email estándar
- **Teléfonos**: Números de teléfono internacionales
- **IPs privadas**: Rangos 10.x.x.x, 172.16-31.x.x, 192.168.x.x

### Reglas de Mensajes de Log

#### ✅ Correcto
```python
# Información útil sin exponer secretos
logger.info("Azure Storage connection established")
logger.info("Database connection successful")
logger.info("API request completed with status: %d", response.status_code)
logger.info("Processing document: %s", safe_value(document_id))
logger.info("User authentication successful for: %s", safe_value(user_email))
```

#### ❌ Incorrecto
```python
# Exponiendo información sensible
logger.info("API Key: %s", api_key)
logger.info("Password: %s", user_password)
logger.info("Connection string: %s", db_connection_string)
logger.info("User email: %s", user_email)  # Sin sanitizar
logger.info("Internal IP: %s", internal_ip)
```

### Configuración de Debug Sanitizado

#### Variables de Entorno
```python
# ❌ Incorrecto - expone secretos
print(f"DEBUG: API_KEY = {os.getenv('API_KEY')}")

# ✅ Correcto - solo muestra estado
print(f"DEBUG: API_KEY = {'SET' if os.getenv('API_KEY') else 'NOT SET'}")
```

#### Configuración de Servicios
```python
# ❌ Incorrecto - expone credenciales
print(f"Database: {db_host}:{db_port} user={db_user}")

# ✅ Correcto - información útil sin secretos
print(f"Database: {db_host}:{db_port} user={'SET' if db_user else 'NOT SET'}")
```

### Implementación en Código Existente

#### 1. Identificar Logs Sensibles
```bash
# Buscar patrones de logging inseguro
grep -r "logger.*password\|logger.*key\|logger.*token" .
grep -r "print.*password\|print.*key\|print.*token" .
```

#### 2. Aplicar Saneamiento
```python
# Antes
logger.info(f"Processing with API key: {api_key}")

# Después
logger.info(f"Processing with API key: {safe_value(api_key)}")
```

#### 3. Usar Loggers Seguros
```python
# Antes
logger = logging.getLogger(__name__)

# Después
from utils.logging_extras import get_safe_logger
logger = get_safe_logger(__name__)
```

### Verificación y Testing

#### Script de Verificación
```bash
# Ejecutar verificación de logs
python scripts/verify_log_sanitization.py
```

#### Pruebas Automatizadas
```python
def test_log_sanitization():
    """Verificar que los logs no contengan información sensible"""
    with captured_logs() as logs:
        process_sensitive_data()
    
    # Verificar que no hay secretos en los logs
    assert '[REDACTED]' in logs
    assert 'api_key' not in logs.lower()
    assert 'password' not in logs.lower()
```

### Checklist de Saneamiento

- [ ] Revisar todos los `print()` statements
- [ ] Sanitizar variables de entorno en debug
- [ ] Usar `safe_value()` para datos sensibles
- [ ] Implementar loggers seguros donde sea apropiado
- [ ] Verificar que no se exponen IPs internas
- [ ] Proteger connection strings y credenciales
- [ ] Redactar información personal de usuarios
- [ ] Probar que las métricas siguen funcionando
