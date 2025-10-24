# Pruebas de VEA WebApp

Este directorio contiene todas las pruebas para la aplicación VEA WebApp, organizadas por tipo y funcionalidad.

## Estructura de Pruebas

```
tests/
├── __init__.py
├── conftest.py              # Configuración y fixtures de pytest
├── test_runner.py           # Script personalizado para ejecutar pruebas
├── README.md               # Esta documentación
├── unit/                   # Pruebas unitarias
│   ├── __init__.py
│   ├── test_models.py      # Pruebas de modelos
│   └── test_forms.py       # Pruebas de formularios
├── functional/             # Pruebas funcionales
│   ├── __init__.py
│   └── test_views.py       # Pruebas de vistas
├── integration/            # Pruebas de integración
│   ├── __init__.py
│   └── test_api_integration.py
└── e2e/                    # Pruebas de extremo a extremo
    ├── __init__.py
    └── test_user_workflows.py
```

## Tipos de Pruebas

### 1. Pruebas Unitarias (`unit/`)
- **Propósito**: Probar componentes individuales de forma aislada
- **Cobertura**: Modelos, formularios, utilidades
- **Ejecución**: Rápidas, sin dependencias externas

**Archivos incluidos:**
- `test_models.py`: Pruebas para todos los modelos de la aplicación
- `test_forms.py`: Pruebas para formularios de validación

### 2. Pruebas Funcionales (`functional/`)
- **Propósito**: Probar funcionalidades completas de la aplicación
- **Cobertura**: Vistas, URLs, templates
- **Ejecución**: Moderadamente rápidas, usan base de datos de prueba

**Archivos incluidos:**
- `test_views.py`: Pruebas para todas las vistas de la aplicación

### 3. Pruebas de Integración (`integration/`)
- **Propósito**: Probar la integración entre componentes
- **Cobertura**: APIs, servicios externos, flujos de datos
- **Ejecución**: Moderadamente lentas, prueban interacciones complejas

**Archivos incluidos:**
- `test_api_integration.py`: Pruebas de integración de APIs y servicios

### 4. Pruebas de Extremo a Extremo (`e2e/`)
- **Propósito**: Probar flujos completos de usuario
- **Cobertura**: Casos de uso reales, navegación completa
- **Ejecución**: Lentas, simulan uso real de la aplicación

**Archivos incluidos:**
- `test_user_workflows.py`: Pruebas de flujos de trabajo completos

## Configuración

### Requisitos
- Python 3.8+
- Django 4.0+
- pytest
- pytest-django
- pytest-cov

### Instalación de dependencias
```bash
pip install pytest pytest-django pytest-cov
```

### Configuración de pytest
El archivo `pytest.ini` contiene la configuración principal:
- Configuración de Django
- Marcadores de pruebas
- Configuración de cobertura
- Opciones de salida

## Ejecución de Pruebas

### Usando el script personalizado
```bash
# Ejecutar todas las pruebas
python tests/test_runner.py

# Ejecutar pruebas específicas
python tests/test_runner.py --type unit
python tests/test_runner.py --type functional
python tests/test_runner.py --type integration
python tests/test_runner.py --type e2e

# Con cobertura
python tests/test_runner.py --coverage

# Con salida detallada
python tests/test_runner.py --verbose

# Ejecutar prueba específica
python tests/test_runner.py --file tests/unit/test_models.py
```

### Usando pytest directamente
```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar por tipo
pytest tests/unit/
pytest tests/functional/
pytest tests/integration/
pytest tests/e2e/

# Con marcadores
pytest -m unit
pytest -m functional
pytest -m integration
pytest -m e2e

# Con cobertura
pytest --cov=apps --cov-report=html
```

## Fixtures Comunes

El archivo `conftest.py` define fixtures reutilizables:

- `client`: Cliente de Django para pruebas
- `test_user`: Usuario de prueba normal
- `admin_user`: Usuario administrador
- `authenticated_client`: Cliente autenticado
- `admin_client`: Cliente con usuario administrador
- `sample_contact`: Contacto de prueba
- `sample_document`: Documento de prueba
- `sample_event`: Evento de prueba
- `sample_donation`: Donación de prueba

## Cobertura de Pruebas

### Objetivo de Cobertura
- **Mínimo**: 80% de cobertura de código
- **Recomendado**: 90%+ de cobertura

### Generar Reporte de Cobertura
```bash
pytest --cov=apps --cov-report=html --cov-report=term-missing
```

El reporte HTML se genera en `htmlcov/index.html`

## Marcos de Pruebas

### Marcadores Disponibles
- `@pytest.mark.unit`: Pruebas unitarias
- `@pytest.mark.functional`: Pruebas funcionales
- `@pytest.mark.integration`: Pruebas de integración
- `@pytest.mark.e2e`: Pruebas de extremo a extremo
- `@pytest.mark.slow`: Pruebas lentas
- `@pytest.mark.fast`: Pruebas rápidas

### Ejemplo de uso
```python
import pytest

@pytest.mark.unit
def test_user_creation():
    """Prueba unitaria de creación de usuario"""
    pass

@pytest.mark.functional
def test_login_view():
    """Prueba funcional de vista de login"""
    pass
```

## Pruebas por Módulo

### Core
- **Modelos**: CustomUser
- **Vistas**: Index, base templates
- **Funcionalidades**: Autenticación, configuración base

### Directory
- **Modelos**: Contact
- **Vistas**: Lista, crear, editar, eliminar contactos
- **Funcionalidades**: CRUD completo de contactos

### Documents
- **Modelos**: Document
- **Vistas**: Lista, subir, editar, eliminar documentos
- **Funcionalidades**: Gestión de archivos, categorización

### Events
- **Modelos**: Event
- **Vistas**: Lista, crear, editar, eliminar eventos
- **Funcionalidades**: Programación de eventos, calendario

### Donations
- **Modelos**: Donation, DonationType
- **Vistas**: Lista, crear, editar, eliminar donaciones
- **Funcionalidades**: Gestión de donaciones, tipos de donación

### Dashboard
- **Vistas**: Dashboard principal
- **Funcionalidades**: Panel de control

### User Settings
- **Vistas**: Perfil de usuario
- **Funcionalidades**: Configuración de usuario

## Mejores Prácticas

### Nomenclatura
- Archivos de prueba: `test_*.py`
- Clases de prueba: `Test*`
- Métodos de prueba: `test_*`

### Organización
- Una clase de prueba por modelo/vista
- Métodos de prueba descriptivos
- Documentación clara de cada prueba

### Datos de Prueba
- Usar factories o fixtures para datos de prueba
- Limpiar datos después de cada prueba
- Usar datos realistas pero no sensibles

### Aserciones
- Usar aserciones específicas
- Probar tanto casos exitosos como de error
- Verificar estado final después de operaciones

## Troubleshooting

### Problemas Comunes

1. **Error de configuración de Django**
   ```bash
   export DJANGO_SETTINGS_MODULE=config.settings.development
   ```

2. **Error de base de datos**
   ```bash
   python manage.py migrate --settings=config.settings.development
   ```

3. **Error de importación**
   - Verificar que `apps/` está en `PYTHONPATH`
   - Verificar que los imports son correctos

4. **Pruebas lentas**
   - Usar `--tb=short` para salida más concisa
   - Ejecutar solo pruebas específicas con `-k`

### Debugging
```bash
# Ejecutar con debug
pytest -s -v

# Ejecutar prueba específica con debug
pytest tests/unit/test_models.py::TestUserModel::test_create_user -s -v
```

## Integración Continua

### GitHub Actions
Las pruebas se ejecutan automáticamente en:
- Push a main
- Pull requests
- Tags de release

### Pre-commit
Configurar hooks para ejecutar pruebas antes de commit:
```bash
pre-commit install
```

## Reportes

### Reportes Automáticos
- Cobertura de código
- Tiempo de ejecución
- Pruebas fallidas
- Pruebas lentas

### Análisis de Tendencias
- Seguimiento de cobertura a lo largo del tiempo
- Identificación de pruebas problemáticas
- Optimización de rendimiento

## Contribución

### Agregar Nuevas Pruebas
1. Crear archivo en el directorio apropiado
2. Seguir convenciones de nomenclatura
3. Agregar documentación
4. Ejecutar pruebas localmente
5. Verificar cobertura

### Mantenimiento
- Revisar pruebas regularmente
- Actualizar cuando cambie la funcionalidad
- Eliminar pruebas obsoletas
- Optimizar pruebas lentas

## Contacto

Para preguntas sobre las pruebas, contactar al equipo de desarrollo o crear un issue en el repositorio. 