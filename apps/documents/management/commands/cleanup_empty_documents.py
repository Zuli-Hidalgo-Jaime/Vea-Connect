"""
Comando de gestión para limpiar documentos vacíos o corruptos
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.documents.models import Document
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia documentos vacíos o corruptos de la base de datos'

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
        
        documents = Document.objects.all()
        
        self.stdout.write(f"Revisando {documents.count()} documentos...")
        
        deleted_count = 0
        error_count = 0
        
        for document in documents:
            # Verificar si el documento está vacío o corrupto
            is_empty = (
                not document.title or 
                document.title.strip() == '' or
                not document.description or 
                document.description.strip() == '' or
                not document.file or
                document.file.name == ''
            )
            
            if is_empty:
                self.stdout.write(f"Documento vacío encontrado: ID={document.id}, title='{document.title}', file='{getattr(document.file, 'name', 'None')}'")
                
                if not dry_run:
                    try:
                        with transaction.atomic():
                            # Eliminar el archivo del storage si existe
                            if document.file:
                                try:
                                    document.file.delete(save=False)
                                    self.stdout.write(f"  ✓ Archivo eliminado del storage")
                                except Exception as e:
                                    self.stdout.write(f"  ⚠ Error eliminando archivo: {e}")
                            
                            # Eliminar el documento de la base de datos
                            document.delete()
                            deleted_count += 1
                            self.stdout.write(f"  ✓ Documento eliminado de la base de datos")
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(f"  ✗ Error eliminando documento: {e}"))
                else:
                    self.stdout.write(f"  [DRY-RUN] Se eliminaría el documento")
                    deleted_count += 1
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RESUMEN:")
        self.stdout.write(f"  Documentos revisados: {documents.count()}")
        self.stdout.write(f"  Documentos eliminados: {deleted_count}")
        self.stdout.write(f"  Errores: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Ejecutado en modo DRY-RUN - no se hicieron cambios reales"))
        else:
            self.stdout.write(self.style.SUCCESS("Proceso completado"))
