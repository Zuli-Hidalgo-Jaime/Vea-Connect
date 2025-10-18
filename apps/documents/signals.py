from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Document
import logging

logger = logging.getLogger(__name__)

# Signal comentado temporalmente para evitar duplicación de procesamiento
# @receiver(post_save, sender=Document)
# def upload_document_to_blob(sender, instance, created, **kwargs):
#     """
#     Signal handler for document upload and processing.
#     Comentado temporalmente para evitar duplicación de procesamiento
#     """
#     pass 