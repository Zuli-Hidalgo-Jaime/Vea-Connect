from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Contact
from utilities.azureblobstorage import upload_to_blob, get_blob_service_client
import json
import os
import io
import zipfile
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Contact)
def upload_contact_to_blob(sender, instance, created, **kwargs):
    """
    Signal handler for contact processing.
    
    This signal automatically:
    1. Uploads contact data to Azure Blob Storage
    2. Generates embeddings for contact information
    3. Stores embeddings in Azure AI Search
    """
    # Verificar si los signals de Azure están deshabilitados
    try:
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            return
    except:
        # Si no se puede acceder a settings, asumir que está deshabilitado
        return
    
    logger.info(f"Contact signal activated for Contact: {instance.id}")
    
    try:
        # Prepare contact data
        contact_data = {
            "id": instance.id,
            "first_name": getattr(instance, 'first_name', ''),
            "last_name": getattr(instance, 'last_name', ''),
            "role": getattr(instance, 'role', ''),
            "ministry": getattr(instance, 'ministry', ''),
            "contact": getattr(instance, 'contact', ''),
            "created_at": instance.created_at.isoformat() if instance.created_at else None
        }
        
        # Create text content for embedding
        # NO incluir 'contact' para evitar indexar números de teléfono
        contact_text = f"{contact_data['first_name']} {contact_data['last_name']} {contact_data['role']} {contact_data['ministry']}"
        contact_text = contact_text.strip()
        
        if contact_text:
            # [DIRECTORY-DIRECT-VECTOR-UPLOAD] Upsert vectorial directo, id estable y sin created_at
            try:
                from apps.embeddings.openai_service import OpenAIService
                from utilities.azure_search_client import get_azure_search_client

                idx_id = f"contact_{instance.id}"

                # Construir contenido de búsqueda desde los campos del contacto
                # NO incluir 'contact' para evitar indexar números de teléfono
                parts = [
                    getattr(instance, "first_name", "") or "",
                    getattr(instance, "last_name", "") or "",
                    getattr(instance, "role", "") or "",
                    getattr(instance, "ministry", "") or "",
                ]
                content = " ".join(p for p in parts if p).strip()

                emb = OpenAIService().generate_embedding(content or "")
                sc = get_azure_search_client()

                # Campos seguros del índice: id, content, embedding, title (evitar props inexistentes)
                doc = {
                    "id": idx_id,
                    "content": content or "",
                    "title": f"{(getattr(instance,'first_name','') or '').strip()} {(getattr(instance,'last_name','') or '').strip()}".strip() or None,
                    "embedding": emb,
                }
                doc = {k: v for k, v in doc.items() if v not in (None, "")}

                logger.warning(f"[DEBUG-DOUBLE-INDEX] Subiendo documento: {json.dumps(doc, default=str)}")
                sc.search_client.upload_documents(documents=[doc])
                logger.info("[DIRECTORY] Upsert OK id=%s", idx_id)
            except Exception as ex:
                logger.warning("[DIRECTORY] Upsert failed: %s", ex)
        
        # Save contact data to blob storage
        json_blob_name = f"contacts/contact_{instance.id}.json"
        
        # Save JSON temporarily
        with open(f"temp_contact_{instance.id}.json", "w", encoding="utf-8") as f:
            json.dump(contact_data, f, ensure_ascii=False, indent=2)
        
        # Upload JSON to blob
        upload_to_blob(f"temp_contact_{instance.id}.json", json_blob_name)
        logger.info(f"Contact data uploaded to blob: {json_blob_name}")
        
        # Create ZIP with contact data (legacy support)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            with open(f"temp_contact_{instance.id}.json", 'rb') as f:
                zip_file.writestr(json_blob_name, f.read())
        
        buffer.seek(0)
        zip_blob_name = f"converted/{json_blob_name}.zip"
        upload_to_blob(buffer, zip_blob_name)
        logger.info(f"Contact ZIP uploaded to blob: {zip_blob_name}")
        
        # Clean up temporary file
        os.remove(f"temp_contact_{instance.id}.json")
        
    except Exception as e:
        logger.error(f"Error in contact signal processing: {e}") 


# [DIRECTORY-DELETE-BY-KEY] Eliminar del índice por clave exacta contact_<id>
@receiver(post_delete, sender=Contact)
def delete_contact_from_search(sender, instance, **kwargs):
    try:
        from utilities.azure_search_client import get_azure_search_client
        sc = get_azure_search_client()
        sc.search_client.delete_documents(documents=[{"id": f"contact_{instance.id}"}])
        # Limpieza de legado (ids numéricos previos)
        try:
            sc.search_client.delete_documents(documents=[{"id": str(instance.id)}])
        except Exception:
            pass
        logger.info("[DIRECTORY] Deleted Search doc contact_%s", instance.id)
    except Exception as ex:
        logger.warning("[DIRECTORY] Delete failed: %s", ex)

    # [DIRECTORY-DELETE-STORAGE-PARITY] Limpieza de blobs (paridad con Eventos) — NO REMOVER NADA EXISTENTE
    try:
        # Respetar el mismo flag que Eventos: si los signals están deshabilitados, no hacer nada
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            pass
        else:
            contact_pk = getattr(instance, 'id', None)
            if contact_pk:
                container = getattr(settings, 'BLOB_CONTAINER_NAME', None)
                if not container:
                    logger.warning("[DIRECTORY-DELETE-STORAGE-PARITY] BLOB_CONTAINER_NAME no configurado")
                else:
                    svc = get_blob_service_client()
                    cc  = svc.get_container_client(container)

                    blob_names = [
                        f"contacts/contact_{contact_pk}.json",
                        f"converted/contacts/contact_{contact_pk}.json.zip",
                    ]
                    for name in blob_names:
                        try:
                            bc = cc.get_blob_client(name)
                            if bc.exists():
                                bc.delete_blob(delete_snapshots='include')
                                logger.info(f"[DIRECTORY-DELETE-STORAGE-PARITY] Blob eliminado: {container}/{name}")
                            else:
                                logger.info(f"[DIRECTORY-DELETE-STORAGE-PARITY] Blob no existe: {container}/{name}")
                        except Exception as e_blob:
                            logger.warning(f"[DIRECTORY-DELETE-STORAGE-PARITY] No se pudo eliminar {name}: {e_blob}")
    except Exception as e:
        logger.warning(f"[DIRECTORY-DELETE-STORAGE-PARITY] Error de limpieza en storage: {e}")