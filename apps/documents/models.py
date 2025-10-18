from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import datetime, timedelta
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from services.storage_service import azure_storage
import logging

logger = logging.getLogger(__name__)

class ProcessingState(models.TextChoices):
    PENDING = 'pending', 'Pendiente'
    CONVERTING = 'converting', 'Convirtiendo'
    INDEXING = 'indexing', 'Indexando'
    READY = 'ready', 'Listo'
    ERROR = 'error', 'Error'

class Document(models.Model):
    CATEGORY_CHOICES = [
        ("eventos_generales", "Eventos generales"),
        ("ministerios", "Ministerios"),
        ("formacion", "Formación"),
        ("campanas", "Campañas"),
        ("avisos_globales", "Avisos globales"),
    ]

    title = models.CharField("Título", max_length=255)
    file = models.FileField("Archivo", upload_to="documents/")
    description = models.TextField("Descripción", blank=True)
    category = models.CharField("Categoría", max_length=32, choices=CATEGORY_CHOICES)
    date = models.DateTimeField("Fecha", blank=True, null=True)
    user = models.ForeignKey(get_user_model(), verbose_name="Usuario", on_delete=models.CASCADE, db_column="user_id", blank=True, null=True)
    file_type = models.CharField("Tipo de archivo", max_length=32, blank=True, null=True)
    is_processed = models.BooleanField("¿Procesado?", default=False)  # type: ignore
    processing_state = models.CharField(
        "Estado de procesamiento", 
        max_length=32, 
        choices=ProcessingState.choices,
        default=ProcessingState.PENDING,
        db_column='processing_status'  # Usar el nombre de columna que existe en Azure
    )
    metadata = models.JSONField("Metadatos", default=dict, blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def sas_url(self):
        """Devuelve una URL SAS temporal para el archivo en Azure Blob Storage."""
        if not self.file:
            return None
        try:
            storage_service = azure_storage
            result = storage_service.get_blob_url(str(self.file.name))
            if result.get('success'):
                return result.get('signed_url')
            return None
        except Exception as e:
            return None

    class Meta:
        ordering = ["-date"]
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

# Señales para manejar el ciclo de vida de los documentos
@receiver(post_delete, sender=Document)
def delete_blob_on_document_delete(sender, instance, **kwargs):
    """Elimina el archivo de Azure Blob Storage cuando se elimina un documento"""
    if instance.file:
        try:
            storage_service = azure_storage
            result = storage_service.delete_blob(instance.file.name)
            if not result.get('success'):
                logger.error(f"Failed to delete blob: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error eliminando blob: {e}")

# @receiver(post_save, sender=Document)
# def trigger_document_processing(sender, instance, created, **kwargs):
#     """Dispara el procesamiento de documentos cuando se crea uno nuevo"""
#     # Comentado temporalmente para evitar duplicación
#     pass 

 