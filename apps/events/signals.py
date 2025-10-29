from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Event
from utilities.azureblobstorage import upload_to_blob, get_blob_service_client
from utilities.embedding_manager import EmbeddingManager
from django.utils import timezone  # [EVENTS-DATETIME-OData-ONLY]
import datetime as _dt  # [EVENTS-DATETIME-OData-ONLY]
import json
import os
import io
import zipfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# [EVENTS-CONTENT-COMPOSER] Incluye fecha y hora en el texto a indexar (sin romper nada)
def _compose_event_content(ev) -> str:
    """Devuelve contenido textual para indexar (incluye fecha y hora).
    No lanza excepciones; rellena solo lo disponible.
    """
    title = (getattr(ev, "title", None) or getattr(ev, "name", None) or "").strip()
    desc = (getattr(ev, "description", None) or getattr(ev, "details", None) or "").strip()
    lugar = (
        getattr(ev, "location", None)
        or getattr(ev, "venue", None)
        or getattr(ev, "place", None)
        or getattr(ev, "address", None)
        or ""
    )
    date_val = (
        getattr(ev, "date", None)
        or getattr(ev, "event_date", None)
        or getattr(ev, "start_date", None)
    )
    time_val = (
        getattr(ev, "time", None)
        or getattr(ev, "start_time", None)
        or getattr(ev, "hour", None)
    )

    def _fmt_date(d):
        try:
            from datetime import date, datetime
            from django.utils import timezone
            if isinstance(d, datetime):
                try:
                    d = timezone.localtime(d)
                except Exception:
                    pass
                return d.strftime("%d/%m/%Y")
            if hasattr(d, "strftime"):
                return d.strftime("%d/%m/%Y")
            return str(d)
        except Exception:
            return str(d)

    def _fmt_time(t):
        try:
            from datetime import time, datetime
            if isinstance(t, datetime):
                t = t.time()
            if hasattr(t, "strftime"):
                return t.strftime("%H:%M")
            return str(t)
        except Exception:
            return str(t)

    parts = [p for p in [title, desc] if p]
    if lugar:
        parts.append(f"Lugar: {lugar}")
    if date_val:
        parts.append(f"Fecha: {_fmt_date(date_val)}")
    if time_val:
        parts.append(f"Hora: {_fmt_time(time_val)}")
    return "\n".join(parts)

# [EVENTS-DATETIME-OData-ONLY]
def _to_odata_dt(dt):
    """Normaliza valores datetime a ISO-8601 con zona (UTC, sufijo Z) para OData.

    Esta función se aplica únicamente al flujo de Eventos para evitar errores
    de validación de tipo Edm.DateTimeOffset en Azure Search.
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        # Si ya trae sufijo Z u offset explícito, respetarlo
        if dt.endswith("Z") or "+" in dt:
            return dt
        try:
            dt = _dt.datetime.fromisoformat(dt)
        except Exception:
            return dt
    if isinstance(dt, _dt.datetime):
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        dt = dt.astimezone(_dt.timezone.utc)
        s = dt.isoformat(timespec="microseconds")
        return s[:-6] + "Z" if s.endswith("+00:00") else s
    return dt

@receiver(post_save, sender=Event)
def upload_event_to_blob(sender, instance, created, **kwargs):
    """
    Signal handler for event processing.
    
    This signal automatically:
    1. Uploads event data to Azure Blob Storage
    2. Generates embeddings for event content
    3. Stores embeddings in Azure AI Search
    """
    # Verificar si los signals de Azure están deshabilitados
    try:
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            return
    except:
        # Si no se puede acceder a settings, asumir que está deshabilitado
        return
    
    logger.info(f"Event signal activated for Event: {instance.id}")
    
    try:
        # Prepare event data
        event_data = {
            "id": instance.id,
            "title": getattr(instance, 'title', ''),
            "description": getattr(instance, 'description', ''),
            "date": str(instance.date) if instance.date else None,
            "time": str(instance.time) if instance.time else None,
            "location": getattr(instance, 'location', ''),
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None
        }
        
        # Create text content for embedding
        event_text = f"{event_data['title']} {event_data['description']} {event_data['location']}"
        event_text = event_text.strip()
        
        if event_text:
            # Generate embedding and store in Azure AI Search
            try:
                # Eliminar referencia a embedding_manager, usar EmbeddingManager() directo si es necesario
                
                # [EVENTS-ALIGN-WITH-DOCS] --- Payload metadata para Search (análogo a Documents) ---
                # ID estable (sin timestamp), y contenido concatenado
                document_id = f"event_{instance.id}"
                event_title = event_data.get('title') or None
                event_desc = event_data.get('description') or None
                event_loc = event_data.get('location') or None
                event_text = " ".join(filter(None, [event_title, event_desc, event_loc])).strip() or None
                # [EVENTS-CONTENT-COMPOSER] concatenar fecha/hora/lugar en content (sin eliminar lo actual)
                try:
                    _extra = _compose_event_content(instance)
                except Exception:
                    _extra = ""
                # [EVENTO-PREFIX] Agregar prefijo para mejorar búsqueda vectorial
                base_content = ((event_text or "") + "\n" + (_extra or "")).strip()
                content_text = "[EVENTO] " + base_content if base_content else ""

                metadata_doc_id = document_id
                index_doc = {
                    "id": metadata_doc_id,
                    "title": event_title,
                    "description": event_desc,
                    "date": event_data.get('date'),   # mantener como string si el índice lo define así
                    "time": event_data.get('time'),   # mantener como string si el índice lo define así
                    "location": event_loc,
                    "content": content_text,
                    "source": "event",
                }
                # Limpia None para no enviar nulos innecesarios
                index_doc = {k: v for k, v in index_doc.items() if v is not None}

                # [EVENTS-METADATA-OFF] Desactivar upsert metadata de Search para EVENTOS (evita 'source' y DateTimeOffset)
                if getattr(settings, "EVENTS_ENABLE_METADATA_UPSERT", False):
                    try:
                        from services.search_index_service import search_index_service
                        if getattr(search_index_service, 'client', None):
                            # Asegurar que no se envíe 'source' y quitar 'id' del metadata
                            index_doc.pop("source", None)
                            logger.info("[EVENTS-METADATA-OFF] Upserting metadata id=%s", metadata_doc_id)
                            meta_without_id = {k: v for k, v in index_doc.items() if k != 'id'}
                            search_index_service.upsert_document(metadata_doc_id, index_doc.get("content", "") or "", meta_without_id)
                    except Exception as _e_upsert_meta:
                        logger.warning(f"[EVENTS-METADATA-OFF] Fallo upsert metadata: {_e_upsert_meta}")
                else:
                    logger.info("[EVENTS-METADATA-OFF] Metadata upsert is disabled for Events (embedding-only).")

                # Create embedding
                try:
                    # [EVENTS-DIRECT-VECTOR-UPLOAD] — upsert vectorial directo, sin created_at
                    from apps.embeddings.openai_service import OpenAIService
                    from utilities.azure_search_client import get_azure_search_client

                    idx_id = document_id
                    text_for_embedding = content_text or ""

                    # 1) Generar embedding DIRECTO (sin pasar por EmbeddingManager)
                    emb = OpenAIService().generate_embedding(text_for_embedding)

                    # 2) Subir a Search DIRECTO, con id estable y SIN created_at
                    sc = get_azure_search_client()
                    doc = {
                        "id": idx_id,
                        "content": text_for_embedding,
                        "embedding": emb,
                    }
                    sc.search_client.upload_documents(documents=[doc])
                    logger.info("[EVENTS-DIRECT-VECTOR-UPLOAD] Vector upsert OK id=%s", idx_id)
                except Exception as e:
                    logger.error("[EVENTS-DIRECT-VECTOR-UPLOAD] Falló vector upsert id=%s: %s", document_id, e)
                    
            except Exception as e:
                logger.error(f"Error creating event embedding: {e}")
        
        # Save event data to blob storage
        json_blob_name = f"events/event_{instance.id}.json"
        
        # Save JSON temporarily
        with open(f"temp_event_{instance.id}.json", "w", encoding="utf-8") as f:
            json.dump(event_data, f, ensure_ascii=False, indent=2)
        
        # Upload JSON to blob
        upload_to_blob(f"temp_event_{instance.id}.json", json_blob_name)
        logger.info(f"Event data uploaded to blob: {json_blob_name}")
        
        # Create ZIP with event data (legacy support)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            with open(f"temp_event_{instance.id}.json", 'rb') as f:
                zip_file.writestr(json_blob_name, f.read())
        
        buffer.seek(0)
        zip_blob_name = f"converted/{json_blob_name}.zip"
        upload_to_blob(buffer, zip_blob_name)
        logger.info(f"Event ZIP uploaded to blob: {zip_blob_name}")
        
        # Clean up temporary file
        os.remove(f"temp_event_{instance.id}.json")
        
    except Exception as e:
        logger.error(f"Error in event signal processing: {e}") 


# [EVENTS-DELETE-LIKE-DOCS]
@receiver(post_delete, sender=Event)
def cleanup_event_assets(sender, instance, **kwargs):
    """Elimina blobs y entradas en Search asociadas a un Evento eliminado.

    - Borra events/event_<id>.json y converted/events/event_<id>.json.zip
    - Borra todos los documentos en Azure Search cuyo id empiece por event_<id>_
    """
    try:
        if getattr(settings, 'DISABLE_AZURE_SIGNALS', False):
            return
    except Exception:
        pass

    event_pk = getattr(instance, 'id', None)
    if not event_pk:
        return

    # 1) Borrar blobs (no falla si no existen)
    try:
        container = getattr(settings, 'BLOB_CONTAINER_NAME', None)
        if container:
            svc = get_blob_service_client()
            container_client = svc.get_container_client(container)
            blob_names = [
                f"events/event_{event_pk}.json",
                f"converted/events/event_{event_pk}.json.zip",
            ]
            for name in blob_names:
                try:
                    bc = container_client.get_blob_client(name)
                    if bc.exists():
                        bc.delete_blob(delete_snapshots='include')
                        logger.info(f"[EVENTS-DELETE-RESCUE] Blob eliminado: {container}/{name}")
                except Exception as _e_blob:
                    logger.warning(f"[EVENTS-DELETE-RESCUE] No se pudo eliminar blob {name}: {_e_blob}")
        else:
            logger.warning("[EVENTS-DELETE-RESCUE] BLOB_CONTAINER_NAME no configurado")
    except Exception as e:
        logger.warning(f"[EVENTS-DELETE-RESCUE] Error de limpieza en storage: {e}")

    # 2) [EVENTS-INDEX-NORMALIZE-ONLY] delete por id estable
    try:
        from utilities.azure_search_client import get_azure_search_client  # el MISMO que usa Documentos
        sc = get_azure_search_client()
        stable_id = f"event_{event_pk}"
        sc.search_client.delete_documents(documents=[{"id": stable_id}])
        logger.info(f"[EVENTS-ID-STABLE-DELETE] Eliminado de Search por ID exacto: {stable_id}")
        # (Opcional) intento adicional para legado con id crudo
        try:
            sc.search_client.delete_documents(documents=[{"id": str(event_pk)}])
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"[EVENTS-ID-STABLE-DELETE] Limpieza en Search falló: {e}")