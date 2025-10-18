# VeaConnect Style Standards

## Resumen

Este directorio contiene los estándares de estilo y documentación para el proyecto VeaConnect. Los estándares están diseñados para mantener consistencia, legibilidad y profesionalismo en el código sin alterar el comportamiento funcional existente.

## Archivos

### `coding_standards.md`
Documentación completa de los estándares de código, incluyendo:
- Docstrings (estilo Google y NumPy)
- Prohibición de emojis
- Estándares de logging
- Herramientas de linting y formateo
- Parches sugeridos

### `examples/`
Directorio con ejemplos prácticos:
- `docstring_examples.py`: Ejemplos de docstrings apropiados
- `logging_examples.py`: Ejemplos de logging profesional

## Principios Fundamentales

### 1. No Breaking Changes
- Los estándares de estilo no deben cambiar el comportamiento del código
- Implementación gradual en código nuevo
- Feature flags para nuevas funcionalidades

### 2. Consistencia
- Un solo estilo en todo el proyecto
- Herramientas automatizadas para mantener consistencia
- Documentación clara y específica

### 3. Profesionalismo
- Sin emojis en código, logs o UI
- Mensajes claros y directos
- Documentación completa

## Implementación

### Fase 1: Documentación ✅
- Estándares establecidos en `coding_standards.md`
- Ejemplos prácticos creados
- Parches sugeridos preparados

### Fase 2: Herramientas (Opcional)
- Instalar herramientas de linting
- Configurar pre-commit hooks
- Integrar con CI/CD

### Fase 3: Aplicación (Futuro)
- Aplicar estándares en código nuevo
- Refactoring gradual de código existente
- Revisión de código con nuevos estándares

## Uso Rápido

### Docstrings
```python
def process_document(file_path: str) -> str:
    """Process a document and extract its content.
    
    Args:
        file_path: Path to the document file.
    
    Returns:
        Processing result message.
    
    Raises:
        FileNotFoundError: If the document file doesn't exist.
        ProcessingError: If document processing fails.
    
    Example:
        >>> result = process_document("sample.pdf")
        >>> print(result)
        'Document processed successfully'
    """
    # Implementation here
    pass
```

### Logging Profesional
```python
# ✅ CORRECTO
logger.info("Document processing completed successfully")
logger.warning("High memory usage detected")
logger.error("Database connection failed")

# ❌ INCORRECTO
logger.info("✅ Document processing completed successfully!")
logger.warning("⚠️  High memory usage detected!")
logger.error("💥 Database connection failed!")
```

### Sin Emojis
```python
# ✅ CORRECTO
def process_data():
    """Process the data and return results."""
    logger.info("Data processed successfully")
    return "Results ready"

# ❌ INCORRECTO
def process_data():
    """🚀 Process the data and return results! 🎉"""
    logger.info("✅ Data processed successfully!")
    return "🎯 Results ready!"
```

## Herramientas Recomendadas

### Linting y Formateo
- **Black**: Formateo automático de código
- **Ruff**: Linter rápido y moderno
- **isort**: Organización de imports
- **mypy**: Verificación de tipos

### Pre-commit Hooks
- Configuración automática de hooks
- Validación antes de commits
- Formateo automático

### Configuración
Ver `parches_sugeridos/04_style_linting.patch` para configuración completa.

## Checklist de Implementación

### Para Nuevo Código
- [ ] Docstrings en inglés (estilo Google o NumPy)
- [ ] Sin emojis en código, logs o UI
- [ ] Mensajes de logging profesionales
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

## Ejemplos Prácticos

### Ejecutar Ejemplos
```bash
# Ejemplos de docstrings
python docs/estilo/examples/docstring_examples.py

# Ejemplos de logging
python docs/estilo/examples/logging_examples.py
```

### Aplicar Parches (Opcional)
```bash
# Aplicar configuración de linting
git apply parches_sugeridos/04_style_linting.patch

# Instalar herramientas
pip install -e ".[dev]"

# Configurar pre-commit
pre-commit install
```

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

## Contacto

Para preguntas sobre los estándares de estilo:
1. Revisar `coding_standards.md`
2. Consultar ejemplos en `examples/`
3. Contactar al equipo de desarrollo

## Changelog

### v1.0.0 (2025-08-12)
- Estándares de estilo establecidos
- Documentación completa creada
- Ejemplos prácticos implementados
- Parches de configuración preparados
- Guías de implementación documentadas
