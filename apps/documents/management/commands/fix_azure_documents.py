"""
Comando de gestión para arreglar documentos en Azure
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.documents.models import Document
from services.storage_service import get_document_storage_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Arregla documentos en Azure que tienen nombres incorrectos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Ejecutando en modo DRY-RUN (sin cambios reales)'))
        
        storage_service = get_document_storage_service()
        documents = Document.objects.all()
        
        self.stdout.write(f"Revisando {documents.count()} documentos...")
        
        fixed_count = 0
        error_count = 0
        
        for document in documents:
            if not document.file:
                continue
                
            current_filename = document.file.name
            self.stdout.write(f"Revisando documento: {document.title} (ID: {document.id})")
            self.stdout.write(f"  Nombre actual en BD: {current_filename}")
            
            # Verificar si el archivo existe con el nombre actual
            exists_result = storage_service.blob_exists(current_filename)
            if exists_result.get('success') and exists_result.get('exists'):
                self.stdout.write(f"  ✓ Archivo encontrado con nombre actual")
                continue
            
            # Buscar archivos que contengan el título del documento
            if document.title:
                title_prefix = f"documents/{document.title}"
                list_result = storage_service.list_blobs(name_starts_with=title_prefix)
                
                if list_result.get('success') and list_result.get('blobs'):
                    # Tomar el archivo más reciente (último de la lista)
                    matching_blobs = list_result.get('blobs', [])
                    if matching_blobs:
                        found_filename = matching_blobs[-1]['name']
                    self.stdout.write(f"  ✓ Archivo encontrado por patrón: {found_filename}")
                    
                    if not dry_run:
                        try:
                            with transaction.atomic():
                                document.file.name = found_filename
                                document.save()
                                fixed_count += 1
                                self.stdout.write(f"  ✓ Nombre actualizado en la base de datos")
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(self.style.ERROR(f"  ✗ Error actualizando: {e}"))
                    else:
                        self.stdout.write(f"  [DRY-RUN] Se actualizaría a: {found_filename}")
                        fixed_count += 1
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ No se encontraron archivos con el patrón: {title_prefix}"))
            else:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Documento sin título"))
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RESUMEN:")
        self.stdout.write(f"  Documentos revisados: {documents.count()}")
        self.stdout.write(f"  Documentos arreglados: {fixed_count}")
        self.stdout.write(f"  Errores: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Ejecutado en modo DRY-RUN - no se hicieron cambios reales"))
        else:
            self.stdout.write(self.style.SUCCESS("Proceso completado"))
