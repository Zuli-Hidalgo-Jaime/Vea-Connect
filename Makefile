# Makefile - VEA Connect Platform
# Fase: Baseline y control de cambios (solo diagnóstico)

# Variables de entorno
PYTHON = python
DJANGO_MANAGE = python manage.py
FUNCTIONS_DIR = functions

# Targets comentados para la fase de diagnóstico
# Estos targets se implementarán en fases posteriores

# Health checks de la plataforma
# make health
# 	- Verificar conectividad a Azure Storage
# 	- Verificar conectividad a Azure AI Search
# 	- Verificar conectividad a Redis
# 	- Verificar conectividad a Azure OpenAI
# 	- Ejecutar health checks de Django
# 	- Ejecutar health checks de Azure Functions

# Pipeline de ingesta de documentos
# make ingest
# 	- Procesar documentos pendientes
# 	- Generar embeddings
# 	- Indexar en Azure AI Search
# 	- Verificar integridad de datos

# Búsqueda semántica con consulta específica
# make search Q="consulta de ejemplo"
# 	- Ejecutar búsqueda vectorial
# 	- Ejecutar búsqueda híbrida
# 	- Mostrar resultados con scores
# 	- Medir latencia de búsqueda

# Limpieza de datos huérfanos (modo dry-run por defecto)
# make cleanup --dry-run
# 	- Detectar blobs huérfanos
# 	- Detectar registros rotos
# 	- Detectar claves Redis obsoletas
# 	- Generar reporte de limpieza

# Suite completa de tests
# make test-all
# 	- Tests unitarios
# 	- Tests de integración
# 	- Tests E2E
# 	- Cobertura de código

# Target por defecto
.PHONY: help
help:
	@echo "VEA Connect Platform - Makefile"
	@echo "================================="
	@echo ""
	@echo "Targets disponibles (comentados para fase de diagnóstico):"
	@echo "  # make health          - Health checks de la plataforma"
	@echo "  # make ingest          - Pipeline de ingesta de documentos"
	@echo "  # make search Q=\"...\"   - Búsqueda semántica"
	@echo "  # make cleanup         - Limpieza de datos huérfanos"
	@echo "  # make test-all        - Suite completa de tests"
	@echo ""
	@echo "Nota: Estos targets están comentados durante la fase de diagnóstico."
	@echo "Se implementarán en fases posteriores de hardening."

# Target para mostrar estado actual
.PHONY: status
status:
	@echo "Estado de la plataforma:"
	@echo "- Rama actual: $(shell git branch --show-current)"
	@echo "- Archivos de diagnóstico: docs/diagnostico/"
	@echo "- Scripts de health: scripts/health/"
	@echo "- Parches sugeridos: parches_sugeridos/"
