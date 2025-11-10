"""
Pipeline de procesamiento asíncrono de documentos
"""
import logging
import tempfile
import os
import re
from datetime import datetime
from django.utils import timezone
from typing import Optional, List, Dict, Any, Tuple
import json

# from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile

from apps.documents.models import Document, ProcessingState
from services.storage_service import azure_storage
from services.search_index_service import search_index_service

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_MAX_CHARS = 1000
DEFAULT_CHUNK_OVERLAP_SEGMENTS = 1
CHUNK_VERSION = 1
FAQ_CHUNK_MODE = "faq"
GENERIC_CHUNK_MODE = "generic"


def _normalize_text(text: str) -> str:
    """Normaliza saltos de línea y espacios consecutivos."""
    return re.sub(r'[ \t]+', ' ', text.replace('\r\n', '\n').replace('\r', '\n')).strip()


def _split_paragraph_into_segments(paragraph: str, max_chars: int) -> List[str]:
    """
    Divide un párrafo largo en segmentos seguros usando límites de oración.
    """
    paragraph = paragraph.strip()
    if not paragraph:
        return []

    if len(paragraph) <= max_chars:
        return [paragraph]

    sentences = re.split(r'(?<=[\.\?\!])\s+(?=[A-ZÁÉÍÓÚÑ0-9])', paragraph)
    segments: List[str] = []
    buffer = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chars:
            # For very long sentences, cut hard limits while preserving words.
            words = sentence.split(' ')
            long_buffer = ""
            for word in words:
                candidate = f"{long_buffer} {word}".strip()
                if len(candidate) > max_chars and long_buffer:
                    segments.append(long_buffer.strip())
                    long_buffer = word
                else:
                    long_buffer = candidate
            if long_buffer:
                segments.append(long_buffer.strip())
            buffer = ""
            continue

        candidate = f"{buffer} {sentence}".strip() if buffer else sentence
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                segments.append(buffer.strip())
            buffer = sentence

    if buffer:
        segments.append(buffer.strip())

    return segments


def split_text_into_faq_sections(text: str) -> Optional[List[str]]:
    """
    Detecta bloques tipo FAQ: encabezado numerado o pregunta, seguido de respuesta.
    Retorna None si no se identifica la estructura.
    """
    normalized = _normalize_text(text)
    if not normalized:
        return None

    lines = [line.strip() for line in normalized.split('\n') if line.strip()]
    faq_sections: List[str] = []
    current_section: List[str] = []

    faq_start_pattern = re.compile(r'^(\d+(\.\d+)*\.?\s+|¿.+\?)')

    for line in lines:
        if faq_start_pattern.match(line):
            if current_section:
                faq_sections.append("\n".join(current_section).strip())
            current_section = [line]
        else:
            if current_section:
                current_section.append(line)
            else:
                # Línea fuera de sección FAQ; abortar este modo
                return None

    if current_section:
        faq_sections.append("\n".join(current_section).strip())

    if len(faq_sections) >= 2:
        return faq_sections
    return None


from typing import Tuple


def split_text_into_chunks(
    text: str,
    max_chars: int = DEFAULT_CHUNK_MAX_CHARS,
    overlap_segments: int = DEFAULT_CHUNK_OVERLAP_SEGMENTS
) -> Tuple[List[str], str]:
    """
    Divide texto largo en bloques manteniendo la coherencia entre párrafos.
    """
    faq_sections = split_text_into_faq_sections(text)
    if faq_sections:
        return _split_chunks_from_sections(faq_sections, max_chars, overlap_segments, True), FAQ_CHUNK_MODE

    normalized = _normalize_text(text)
    if not normalized:
        return [], GENERIC_CHUNK_MODE

    raw_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', normalized) if p.strip()]

    # Fusionar encabezados/preguntas con su siguiente párrafo para no separarlos
    merged_paragraphs: List[str] = []
    i = 0
    while i < len(raw_paragraphs):
        paragraph = raw_paragraphs[i]
        if i + 1 < len(raw_paragraphs):
            next_paragraph = raw_paragraphs[i + 1]
        else:
            next_paragraph = ""

        if (
            next_paragraph
            and len(paragraph) <= max_chars
            and paragraph.rstrip().endswith(("?", ":", "¿"))
        ):
            combined = f"{paragraph}\n\n{next_paragraph}"
            merged_paragraphs.append(combined.strip())
            i += 2
        else:
            merged_paragraphs.append(paragraph)
            i += 1

    return (
        _split_chunks_from_sections(merged_paragraphs, max_chars, overlap_segments, False),
        GENERIC_CHUNK_MODE,
    )


def _split_chunks_from_sections(
    sections: List[str],
    max_chars: int,
    overlap_segments: int,
    respect_boundaries: bool
) -> List[str]:
    segments: List[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if respect_boundaries:
            segments.append(section)
            continue
        if len(section) <= max_chars:
            segments.append(section)
        else:
            segments.extend(_split_paragraph_into_segments(section, max_chars))

    if not segments:
        return []

    chunks: List[str] = []
    current_segments: List[str] = []
    current_length = 0
    separator_len = 2  # len("\n\n")

    for segment in segments:
        segment_length = len(segment)
        added_length = segment_length if not current_segments else segment_length + separator_len
        if current_segments and current_length + added_length > max_chars:
            chunk_text = "\n\n".join(current_segments).strip()
            if chunk_text:
                chunks.append(chunk_text)
            if overlap_segments > 0 and len(current_segments) >= overlap_segments:
                current_segments = current_segments[-overlap_segments:]
            else:
                current_segments = []
            current_length = sum(len(s) for s in current_segments)
            if current_segments:
                current_length += separator_len * (len(current_segments) - 1)

        current_segments.append(segment)
        current_length = sum(len(s) for s in current_segments)
        if len(current_segments) > 1:
            current_length += separator_len * (len(current_segments) - 1)

    if current_segments:
        chunk_text = "\n\n".join(current_segments).strip()
        if chunk_text:
            chunks.append(chunk_text)

    # Asegurar que exista al menos un chunk
    if not chunks and sections:
        combined = "\n\n".join(sections).strip()
        chunks = [combined] if combined else []

    if respect_boundaries and len(chunks) > 1:
        adjusted_chunks: List[str] = []
        carry_over = None
        for i, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if carry_over:
                if chunk:
                    chunk = f"{carry_over}\n\n{chunk}"
                else:
                    chunk = carry_over
                carry_over = None

            if chunk.rstrip().endswith('?') and i < len(chunks) - 1:
                carry_over = chunk
                continue

            if chunk:
                adjusted_chunks.append(chunk)

        if carry_over:
            if adjusted_chunks:
                adjusted_chunks[-1] = f"{adjusted_chunks[-1]}\n\n{carry_over}"
            else:
                adjusted_chunks.append(carry_over)
        chunks = adjusted_chunks

    return chunks


def get_document_chunk_ids(document_id: int, metadata: Optional[Dict[str, Any]]) -> List[str]:
    """
    Construye la lista de IDs en Azure Search para un documento chunked.
    """
    source_id = f"doc_{document_id}"
    if not metadata or not isinstance(metadata, dict):
        return [source_id]

    chunk_info = metadata.get('chunking') or {}
    chunk_count = chunk_info.get('chunk_count')
    if isinstance(chunk_count, int) and chunk_count > 1:
        chunk_ids = [f"{source_id}_chunk_{i:03d}" for i in range(chunk_count)]
        # Asegurar que la llave legacy también sea eliminada por si existe
        chunk_ids.append(source_id)
        return sorted(set(chunk_ids))
    return [source_id]


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
        
        chunk_texts, chunk_mode = split_text_into_chunks(
            content,
            max_chars=DEFAULT_CHUNK_MAX_CHARS,
            overlap_segments=DEFAULT_CHUNK_OVERLAP_SEGMENTS
        )
        if not chunk_texts:
            chunk_texts = [content]
            chunk_mode = GENERIC_CHUNK_MODE

        total_chunks = len(chunk_texts)
        source_id = f"doc_{document.id}"

        # Intentar limpiar cualquier índice previo (legacy)
        try:
            search_index_service.delete_document(source_id)
        except Exception:
            pass

        # También limpiar posibles chunks antiguos usando metadata existente
        existing_chunk_ids = get_document_chunk_ids(document.id, document.metadata)
        for old_chunk_id in existing_chunk_ids:
            if old_chunk_id != source_id:  # ya se intentó eliminar arriba
                try:
                    search_index_service.delete_document(old_chunk_id)
                except Exception:
                    pass

        vector_lengths: List[int] = []
        index_success = True
        
        logger.info(json.dumps({
            "stage": "chunking",
            "doc_id": str(document.id),
            "filename": document.file.name,
            "chunks": total_chunks,
            "max_chars": DEFAULT_CHUNK_MAX_CHARS,
            "overlap_segments": DEFAULT_CHUNK_OVERLAP_SEGMENTS
        }))
        
        # Paso 5: Indexar en Azure Search con chunks
        start_time = datetime.now()
        
        # Usar el ID del documento como identificador único
        document_vector_id = source_id
        
        # Normalizar fecha a Edm.DateTimeOffset (UTC, con sufijo Z)
        created_dt = document.date or timezone.now()
        if timezone.is_naive(created_dt):
            try:
                created_dt = timezone.make_aware(created_dt, timezone=timezone.utc)  # type: ignore[arg-type]
            except Exception:
                created_dt = timezone.now()
        created_at_iso = created_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        for idx, chunk_text in enumerate(chunk_texts):
            chunk_id = document_vector_id if total_chunks == 1 else f"{document_vector_id}_chunk_{idx:03d}"

            chunk_metadata_payload = {
                'title': document.title,
                'created_at': created_at_iso,
                'metadata': json.dumps({
                    'category': document.category,
                    'description': document.description,
                    'filename': document.file.name,
                    'ocr_text': ocr_text if idx == 0 else '',
                    'source_id': document_vector_id,
                    'chunk_index': idx,
                    'chunk_count': total_chunks,
                    'chunk_mode': chunk_mode
                })
            }

            vector = generate_embeddings(chunk_text)
            vector_lengths.append(len(vector) if isinstance(vector, list) else 0)
            if isinstance(vector, list) and vector:
                chunk_metadata_payload['embedding'] = vector

            chunk_success = search_index_service.upsert_document(
                chunk_id,
                chunk_text,
                chunk_metadata_payload
            )
            index_success = index_success and chunk_success

        logger.info(json.dumps({
            "stage": "embeddings",
            "doc_id": str(document.id),
            "filename": document.file.name,
            "status": "success" if index_success else "partial",
            "chunks": total_chunks,
            "vector_lengths": vector_lengths,
            "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
        }))
        
        if index_success:
            document.processing_state = ProcessingState.READY
            document.is_processed = True
            # Actualizar metadata con información de chunking
            doc_metadata = document.metadata if isinstance(document.metadata, dict) else {}
            doc_metadata = doc_metadata or {}
            doc_metadata['chunking'] = {
                'version': CHUNK_VERSION,
                'chunk_count': total_chunks,
                'max_chars': DEFAULT_CHUNK_MAX_CHARS,
                'overlap_segments': DEFAULT_CHUNK_OVERLAP_SEGMENTS,
                'mode': chunk_mode,
                'last_indexed_at': timezone.now().isoformat()
            }
            document.metadata = doc_metadata
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
                try:
                    import fitz  # type: ignore
                    with fitz.open(temp_file_path) as pdf_doc:
                        fallback_text = [page.get_text("text") for page in pdf_doc]
                    fallback_combined = "\n".join(fallback_text).strip()
                    if fallback_combined and len(fallback_combined) > len(content or ""):
                        logger.info(
                            "Fallback PyMuPDF used for PDF %s (length %s -> %s)",
                            filename,
                            len(content or ""),
                            len(fallback_combined),
                        )
                        content = fallback_combined
                except ImportError:
                    logger.warning("PyMuPDF not installed; cannot apply PDF fallback for %s", filename)
                except Exception as fallback_exc:
                    logger.warning("PyMuPDF fallback failed for %s: %s", filename, fallback_exc)
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
        chunk_ids = get_document_chunk_ids(document.id, document.metadata)
        for chunk_id in chunk_ids:
            search_index_service.delete_document(chunk_id)
        
        # Reprocesar (comentado ya que no es una tarea de Celery)
        # return process_document_async.delay(document_id)
        return process_document_async(document_id)
        
    except Document.DoesNotExist:
        logger.error(f"Documento no encontrado para reprocesar: {document_id}")
        return False
    except Exception as e:
        logger.error(f"Error reprocesando documento {document_id}: {str(e)}")
        return False
