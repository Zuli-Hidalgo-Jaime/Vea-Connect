from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Donation
from utilities.azureblobstorage import upload_to_blob, get_blob_service_client
from utilities.embedding_manager import EmbeddingManager
import json
import os
import io
import zipfile
import tempfile
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def _compose_donation_content(dn) -> str:
    """
    Devuelve texto plano con Banco y CLABE si existen en el modelo de Donación.
    No lanza excepciones; rellena solo lo disponible.
    """
    bank = (
        getattr(dn, "bank", None)
        or getattr(dn, "banco", None)
        or getattr(dn, "bank_name", None)
        or ""
    )
    clabe = (
        getattr(dn, "clabe", None)
        or getattr(dn, "clabe_interbancaria", None)
        or getattr(dn, "account_clabe", None)
        or getattr(dn, "account_number", None)
        or ""
    )
    parts = []
    if bank:
        parts.append(f"Banco: {bank}")
    if clabe:
        parts.append(f"CLABE: {clabe}")
    return "\n".join(parts)


def _json_default(o):
    try:
        from enum import Enum
        from datetime import date, datetime, time
        import decimal
        if isinstance(o, Enum):
            return getattr(o, "value", str(o))
        if isinstance(o, (datetime, date, time)):
            return o.isoformat()
        if isinstance(o, decimal.Decimal):
            return float(o)
        return str(o)
    except Exception:
        return str(o)

@receiver(post_save, sender=Donation)
def upload_donation_to_blob(sender, instance, created, **kwargs):
    # Verificar si los signals de Azure están deshabilitados
    try:
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            return
    except:
        # Si no se puede acceder a settings, asumir que está deshabilitado
        return
    
    try:
        # Prepare donation data
        donation_data = {
            "id": instance.id,
            "title": getattr(instance, 'title', ''),
            "description": getattr(instance, 'description', ''),
            "amount": str(getattr(instance, 'amount', '') or ''),
            "donation_type": str(getattr(instance, 'donation_type', '') or ''),
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None
        }
        
        # Create text content for embedding
        donation_text = f"{donation_data['title']} {donation_data['description']} {donation_data['donation_type']}"
        donation_text = donation_text.strip()
        
        if donation_text:
            # [DONATIONS-DIRECT-VECTOR-UPLOAD] — Paridad con Eventos (upsert vectorial directo, id estable, sin created_at)
            try:
                if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
                    pass
                else:
                    from apps.embeddings.openai_service import OpenAIService
                    from utilities.azure_search_client import get_azure_search_client

                    idx_id = f"donation_{instance.id}"

                    # Construir texto para búsqueda (conservando donation_text ya armado)
                    parts = [
                        getattr(instance, "title", "") or "",
                        getattr(instance, "description", "") or "",
                        getattr(instance, "location", "") or "",
                        str(getattr(instance, "amount", "") or ""),
                        getattr(instance, "entity", "") or "",
                    ]
                    content = " ".join(p for p in parts if p).strip() or donation_text
                    # Concatenar Banco/CLABE al texto indexado (sin alterar el resto)
                    try:
                        extra = _compose_donation_content(instance)
                    except Exception:
                        extra = ""
                    final_text = (content + ("\n" + extra if extra else "")).strip()

                    emb = OpenAIService().generate_embedding(final_text or "")
                    sc  = get_azure_search_client()

                    # Subir directo sin created_at para evitar Edm.DateTimeOffset
                    doc = {
                        "id": idx_id,
                        "content": final_text or "",
                        "title": getattr(instance, "title", None) or None,
                        "description": getattr(instance, "description", None) or None,
                        "embedding": emb,
                    }
                    doc = {k: v for k, v in doc.items() if v not in (None, "")}
                    sc.search_client.upload_documents(documents=[doc])
                    logger.info("[DONATIONS] Upsert OK id=%s", idx_id)
            except Exception as ex:
                logger.warning("[DONATIONS] Upsert failed: %s", ex)
        
        # Save donation data to blob storage
        json_blob_name = f"donations/donation_{instance.id}.json"
        
        # Create temporary file using tempfile module
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            # Usar default=_json_default para serializar Enum/fecha/Decimal de forma segura
            try:
                json.dump(donation_data, temp_file, ensure_ascii=False, indent=2, default=_json_default)
            except TypeError:
                # Fallback defensivo
                json.dump(donation_data, temp_file, ensure_ascii=False, indent=2, default=str)
            temp_file_path = temp_file.name
        
        try:
            # Upload JSON to blob
            upload_to_blob(temp_file_path, json_blob_name)
            logger.info(f"Donation data uploaded to blob: {json_blob_name}")
            
            # Create ZIP with donation data (legacy support)
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                with open(temp_file_path, 'rb') as f:
                    zip_file.writestr(json_blob_name, f.read())
            
            buffer.seek(0)
            zip_blob_name = f"converted/{json_blob_name}.zip"
            upload_to_blob(buffer, zip_blob_name)
            logger.info(f"Donation ZIP uploaded to blob: {zip_blob_name}")
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        # [DONATIONS-BLOB-SAVE-PARITY] Guardado de JSON y ZIP en Blob (paridad con Eventos/Directorio)
        try:
            # Respeta el flag global para deshabilitar señales en despliegues
            if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
                pass
            else:
                donation_id = getattr(instance, "id", None)
                if donation_id is not None:
                    # 1) Construir el payload JSON (solo para almacenamiento; NO se manda a Search)
                    created_at_val = getattr(instance, "created_at", None)
                    updated_at_val = getattr(instance, "updated_at", None)
                    donation_json = {
                        "id": donation_id,
                        "title": getattr(instance, "title", "") or "",
                        "description": getattr(instance, "description", "") or "",
                        "amount": str(getattr(instance, "amount", "")) or "",
                        "donation_type": getattr(instance, "donation_type", "") or getattr(instance, "type", "") or "",
                        "entity": getattr(instance, "entity", "") or "",
                        "location": getattr(instance, "location", "") or "",
                        # created_at/updated_at aquí son inofensivos porque SOLO van a Blob
                        "created_at": created_at_val.isoformat() if created_at_val else None,
                        "updated_at": updated_at_val.isoformat() if updated_at_val else None,
                    }

                    # 2) Subir JSON a Blob
                    json_blob_name = f"donations/donation_{donation_id}.json"
                    tmp_path = f"temp_donation_{donation_id}.json"
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        try:
                            json.dump(donation_json, f, ensure_ascii=False, indent=2, default=_json_default)
                        except TypeError:
                            json.dump(donation_json, f, ensure_ascii=False, indent=2, default=str)

                    upload_to_blob(tmp_path, json_blob_name)

                    # 3) Subir ZIP "converted" con el mismo JSON dentro (compatibilidad)
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w") as zf:
                        with open(tmp_path, "rb") as src:
                            zf.writestr(json_blob_name, src.read())
                    buf.seek(0)
                    upload_to_blob(buf, f"converted/{json_blob_name}.zip")

                    # 4) Limpieza de temporal
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

                    logging.getLogger(__name__).info("[DONATIONS-BLOB-SAVE-PARITY] Subidos %s y converted/%s.zip",
                                                     json_blob_name, json_blob_name)
        except Exception as e_blob:
            logging.getLogger(__name__).warning("[DONATIONS-BLOB-SAVE-PARITY] Error subiendo blobs: %s", e_blob)

    except Exception as e:
        logger.error(f"Error in donation signal processing: {e}") 


@receiver(post_delete, sender=Donation)
def delete_donation_cleanup(sender, instance, **kwargs):
    # [DONATIONS-DELETE-BY-KEY] — Índice
    try:
        from utilities.azure_search_client import get_azure_search_client
        sc = get_azure_search_client()
        stable = f"donation_{instance.id}"
        sc.search_client.delete_documents(documents=[{"id": stable}])
        try:
            sc.search_client.delete_documents(documents=[{"id": str(instance.id)}])
        except Exception:
            pass
        logger.info("[DONATIONS] Deleted Search doc %s", stable)
    except Exception as ex:
        logger.warning("[DONATIONS] Delete Search failed: %s", ex)

    # [DONATIONS-DELETE-STORAGE] — Blobs
    try:
        if not getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            container = getattr(settings, 'BLOB_CONTAINER_NAME', None)
            if container:
                svc = get_blob_service_client()
                cc  = svc.get_container_client(container)
                for name in [
                    f"donations/donation_{instance.id}.json",
                    f"converted/donations/donation_{instance.id}.json.zip",
                ]:
                    try:
                        bc = cc.get_blob_client(name)
                        if bc.exists():
                            bc.delete_blob(delete_snapshots='include')
                            logger.info("[DONATIONS] Blob eliminado: %s/%s", container, name)
                    except Exception as e_blob:
                        logger.warning("[DONATIONS] No se pudo eliminar %s: %s", name, e_blob)
            else:
                logger.warning("[DONATIONS] BLOB_CONTAINER_NAME no configurado")
    except Exception as ex:
        logger.warning("[DONATIONS] Error de limpieza en storage: %s", ex)