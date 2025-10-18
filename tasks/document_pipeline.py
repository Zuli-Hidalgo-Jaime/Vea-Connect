"""
Pipeline de procesamiento asíncrono de documentos
"""
import logging
import tempfile
import os
from datetime import datetime
from django.utils import timezone
from typing import Optional, List
import json

# from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile

from apps.documents.models import Document, ProcessingState
from services.storage_service import azure_storage
from services.search_index_service import search_index_service

logger = logging.getLogger(__name__)


# @shared_task(bind=True, max_retries=3)
def process_document_async(document_id: int) -> bool:
    """
    Procesa un documento de forma asíncrona
    
    Args:
        document_id: ID del documento a procesar
        
    Returns:
        bool: True si el procesamiento fue exitoso
    """
    try:
        # Obtener el documento
        document = Document.objects.get(id=document_id)
        
        # Actualizar estado a converting
        document.processing_state = ProcessingState.CONVERTING
        document.save()
        
        logger.info(json.dumps({
            "stage": "start",
            "doc_id": str(document.id),
            "filename": document.file.name,
            "status": "started"
        }))
        
        # Paso 1: Descargar archivo original o usar texto convertido como fallback
        start_time = datetime.now()
        # Normalizar nombre de blob para evitar prefijos duplicados heredados
        blob_name = getattr(getattr(document, 'file', None), 'name', '') or ''
        logger.debug("PIPELINE DEBUG: document.file.name = '%s'", blob_name)
        temp_file = None
        used_converted_text = False
        ocr_text: Optional[str] = None
        try:
            if blob_name.startswith('documents/documents/'):
                blob_name = blob_name[len('documents/'):]
                logger.debug("PIPELINE DEBUG: blob_name sin doble prefijo = '%s'", blob_name)
            # Intentar resolver antes de descargar
            try:
                resolved = azure_storage.resolve_blob_name(blob_name)
                logger.debug("PIPELINE DEBUG: resolved = '%s'", resolved)
            except Exception as e:
                resolved = None
                logger.debug("PIPELINE DEBUG: Error resolviendo blob_name: %s", e)
            final_name = resolved or blob_name
            logger.debug("PIPELINE DEBUG: Intentando descargar: '%s'", final_name)
            temp_file = azure_storage.download_to_tempfile(final_name)
        except Exception:
            # Reintento por prefijo estable tomando el nombre base sin extensión
            from os.path import basename
            base = basename(blob_name)
            base_no_ext = base.rsplit('.', 1)[0] if base else ''
            tokens = base_no_ext.split('_') if base_no_ext else []
            # Prefijo estable: base sin los dos sufijos finales (timestamp y hash)
            if len(tokens) >= 3:
                stable = '_'.join(tokens[:-2])
            elif len(tokens) >= 1:
                stable = tokens[0]
            else:
                stable = ''

            candidate = None
            if stable:
                prefix = f"documents/{stable}_"
                lst = azure_storage.list_blobs(name_starts_with=prefix)
                blobs = lst.get('blobs') or []
                if blobs:
                    try:
                        # Orden descendente por fecha para tomar el más reciente
                        blobs = sorted(blobs, key=lambda b: b.get('last_modified') or '', reverse=True)
                    except Exception:
                        pass
                    candidate = blobs[0]['name']

            if candidate:
                # Descargar usando el candidato encontrado (sin modificar BD)
                temp_file = azure_storage.download_to_tempfile(candidate)
            else:
                # Fallback: intentar usar el texto convertido si existe
                converted_candidate = None
                if stable:
                    conv_prefix = f"converted/documents/{stable}_"
                    conv_lst = azure_storage.list_blobs(name_starts_with=conv_prefix)
                    conv_blobs = conv_lst.get('blobs') or []
                    if conv_blobs:
                        try:
                            conv_blobs = sorted(conv_blobs, key=lambda b: b.get('last_modified') or '', reverse=True)
                        except Exception:
                            pass
                        converted_candidate = conv_blobs[0]['name']
                if converted_candidate:
                    # Descargar el TXT convertido y cargar su contenido como OCR
                    txt_path = azure_storage.download_to_tempfile(converted_candidate)
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as fh:
                            ocr_text = fh.read()
                        used_converted_text = True
                    finally:
                        try:
                            if os.path.exists(txt_path):
                                os.unlink(txt_path)
                        except Exception:
                            pass
                else:
                    # Último recurso: intentar con documents/{base} directo
                    if base:
                        alt = f"documents/{base}"
                        try:
                            temp_file = azure_storage.download_to_tempfile(alt)
                        except Exception:
                            # Sin original ni convertido en Azure: abortar
                            raise
        
        logger.info(json.dumps({
            "stage": "download",
            "doc_id": str(document.id),
            "filename": document.file.name,
            "status": "success",
            "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
        }))
        
        # Paso 2: Obtener texto (OCR o convertido)
        start_time = datetime.now()
        document.processing_state = ProcessingState.CONVERTING
        document.save()
        
        if not used_converted_text:
            # convert_document_to_text espera un ContentFile; temp_file es un path (str)
            # Cargar el archivo temporal y envolverlo en ContentFile
            try:
                assert temp_file is not None
                with open(temp_file, 'rb') as _fh:
                    content_file = ContentFile(_fh.read(), name=os.path.basename(document.file.name))
            finally:
                # Limpiar el archivo temporal descargado
                try:
                    if temp_file and os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception:
                    pass

            ocr_text = convert_document_to_text(content_file)

        # Construir content con toda la información para búsquedas semánticas
        content = f"{document.title} {document.description} {document.category} {ocr_text or ''}".strip()
        
        logger.info(json.dumps({
            "stage": "conversion",
            "doc_id": str(document.id),
            "filename": document.file.name,
            "status": "success",
            "content_length": len(content),
            "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
        }))
        
        # Paso 3: Guardar contenido convertido
        # Limpiar doble prefijo antes de generar nombre del archivo convertido
        clean_filename = document.file.name
        while clean_filename.startswith('documents/documents/'):
            clean_filename = clean_filename[len('documents/'):]
        converted_filename = f"converted/{clean_filename.replace('.', '_')}.txt"
        converted_content = ContentFile(content.encode('utf-8'), name=converted_filename)
        
        # Subir usando upload_data (no existe azure_storage.upload)
        try:
            azure_storage.upload_data(
                converted_content.read(),
            converted_filename,
                content_type='text/plain; charset=utf-8',
            metadata={
                'original_document_id': str(document.id),
                'conversion_date': datetime.now().isoformat()
            }
        )
        except Exception as _e:
            logger.warning(f"No se pudo subir el texto convertido a storage: {_e}")
        
        # Paso 4: Generar embeddings e indexar
        start_time = datetime.now()
        document.processing_state = ProcessingState.INDEXING
        document.save()
        
        vector = generate_embeddings(content)
        
        logger.info(json.dumps({
            "stage": "embeddings",
            "doc_id": str(document.id),
            "filename": document.file.name,
            "status": "success",
            "vector_length": len(vector),
            "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
        }))
        
        # Paso 5: Indexar en Azure Search
        start_time = datetime.now()
        
        # Usar el ID del documento como identificador único
        document_vector_id = f"doc_{document.id}"
        
        # Normalizar fecha a Edm.DateTimeOffset (UTC, con sufijo Z)
        created_dt = document.date or timezone.now()
        if timezone.is_naive(created_dt):
            try:
                created_dt = timezone.make_aware(created_dt, timezone=timezone.utc)  # type: ignore[arg-type]
            except Exception:
                created_dt = timezone.now()
        created_at_iso = created_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        metadata = {
            'title': document.title,
            'created_at': created_at_iso,
            'metadata': json.dumps({
            'category': document.category,
            'description': document.description,
                'filename': document.file.name,
                'ocr_text': ocr_text or ''
            })
        }
        # Adjuntar embedding solo si es real (None => sin OpenAI configurado)
        if isinstance(vector, list) and vector:
            metadata['embedding'] = vector
        
        success = search_index_service.upsert_document(
            document_vector_id,
            content,
            metadata
        )
        
        if success:
            document.processing_state = ProcessingState.READY
            document.is_processed = True
            document.save()
            
            logger.info(json.dumps({
                "stage": "indexing",
                "doc_id": str(document.id),
                "filename": document.file.name,
                "status": "success",
                "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
            }))
            
            return True
        else:
            document.processing_state = ProcessingState.ERROR
            document.save()
            
            logger.error(json.dumps({
                "stage": "indexing",
                "doc_id": str(document.id),
                "filename": document.file.name,
                "status": "error",
                "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
            }))
            
            return False
            
    except Document.DoesNotExist:
        logger.error(f"Documento no encontrado: {document_id}")
        return False
    except Exception as e:
        logger.error(f"Error procesando documento {document_id}: {str(e)}")
        
        # Actualizar estado a error
        try:
            document = Document.objects.get(id=document_id)
            document.processing_state = ProcessingState.ERROR
            document.save()
        except:
            pass
        
        # Retry si es posible (comentado ya que no es una tarea de Celery)
        # if self.request.retries < self.max_retries:
        #     raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return False


def convert_document_to_text(file_content: ContentFile) -> str:
    """
    Convierte un documento a texto usando Azure Vision
    
    Args:
        file_content: Contenido del archivo
        
    Returns:
        str: Texto extraído del documento
    """
    try:
        import tempfile
        import os
        from apps.vision.azure_vision_service import AzureVisionService
        
        # Crear archivo temporal para procesar
        safe_name = getattr(file_content, 'name', None)
        # Crear archivo temporal para procesar (usar extensión si está disponible)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(safe_name or '')[1]) as temp_file:
            temp_file.write(file_content.read())
            temp_file_path = temp_file.name
        
        try:
            # Inicializar servicio de Azure Vision
            vision_service = AzureVisionService()
            
            # Determinar extensión real (preferir la del nombre, si no la del temp)
            ext = os.path.splitext(safe_name or '')[1].lower() or os.path.splitext(temp_file_path)[1].lower()
            filename = (safe_name or os.path.basename(temp_file_path)).lower()
            
            # Extraer texto según el tipo de archivo
            if ext == '.txt':
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif ext == '.pdf':
                content = vision_service.extract_text_from_pdf(temp_file_path)
            elif ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif'):
                content = vision_service.extract_text_from_image(temp_file_path)
            elif ext in ('.doc', '.docx'):
                # Por ahora, placeholder para documentos de Word
                content = f"Contenido extraído de Word: {filename}"
            else:
                content = f"Contenido del archivo: {filename}"
            
            logger.info(f"Texto extraído exitosamente de {filename}, longitud: {len(content)}")
            return content
            
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error convirtiendo documento {file_content.name}: {str(e)}")
        return f"Error al extraer contenido: {str(e)}"


def generate_embeddings(text: str) -> List[float]:
    """
    Genera embeddings para el texto
    
    Args:
        text: Texto para generar embeddings
        
    Returns:
        List[float]: Vector de embeddings
    """
    try:
        from apps.embeddings.openai_service import OpenAIService
        svc = OpenAIService()
        vec = svc.generate_embedding(text)
        # Asegurar lista de floats
        if isinstance(vec, list) and vec:
            return vec
        return []  # Sin embedding si no vino válido
    except Exception as e:
        # Si OpenAI no está configurado o falla, no devolvemos vector dummy
        logger.warning(f"Embeddings no generados (fallback a texto): {str(e)}")
        return []


# @shared_task
def reprocess_document(document_id: int) -> bool:
    """
    Reprocesa un documento existente
    
    Args:
        document_id: ID del documento a reprocesar
        
    Returns:
        bool: True si el reprocesamiento fue exitoso
    """
    try:
        document = Document.objects.get(id=document_id)
        
        # Eliminar caché existente (comentado ya que DocumentVectorCache no existe)
        # try:
        #     document.vector_cache.delete()
        # except DocumentVectorCache.DoesNotExist:
        #     pass
        
        # Eliminar del índice de búsqueda
        document_vector_id = f"doc_{document.id}"
        search_index_service.delete_document(document_vector_id)
        
        # Reprocesar (comentado ya que no es una tarea de Celery)
        # return process_document_async.delay(document_id)
        return process_document_async(document_id)
        
    except Document.DoesNotExist:
        logger.error(f"Documento no encontrado para reprocesar: {document_id}")
        return False
    except Exception as e:
        logger.error(f"Error reprocesando documento {document_id}: {str(e)}")
        return False
