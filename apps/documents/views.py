# apps/documents/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import DocumentForm
from django.contrib.auth.decorators import login_required
from .models import Document, ProcessingState
import mimetypes
import datetime
from django.http import HttpResponseRedirect, FileResponse, Http404, HttpResponse, JsonResponse
from django.db import models
from django.db.models import Q
from django.conf import settings
import logging
import requests
from functools import reduce
import operator
from services.storage_service import azure_storage
import os
from pathlib import Path
from django.core.files.base import ContentFile
from django.utils import timezone
import json
from tasks.document_pipeline import convert_document_to_text, generate_embeddings
from services.search_index_service import search_index_service

logger = logging.getLogger(__name__)


@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            if not getattr(document, 'date', None):
                document.date = timezone.now()

            uploaded_file = request.FILES.get('file', None)
            if not uploaded_file:
                messages.error(request, "Debes seleccionar un archivo para subir el documento.")
                return render(request, 'documents/create.html', {'form': form})

            # [FIX-CREATE-SAVE] Guardar el archivo ORIGINAL sin consumir el stream
            document.is_processed = False
            try:
                if hasattr(uploaded_file, 'seek'):
                    try:
                        uploaded_file.seek(0)
                    except Exception:
                        pass
                document.file = uploaded_file  # type: ignore[assignment]
                document.save()
            except Exception as err:
                logger.error(f"Error guardando documento inicial: {err}")
                messages.error(request, "No se pudo crear el documento.")
                return render(request, 'documents/create.html', {'form': form})

            # [FIX-CREATE-OCR] Asegurar instancia fresca tras guardar
            try:
                document.refresh_from_db()
            except Exception:
                pass

            # Helper idéntico al usado en EDIT
            def _upload_blob_overwrite(container: str, blob_name: str, data: bytes, content_type: str) -> str:
                if not azure_storage or not getattr(azure_storage, 'client', None):
                    raise Exception('Azure Storage client no disponible')
                from azure.storage.blob import ContentSettings as _ContentSettings
                blob_client = azure_storage.client.get_blob_client(container=container, blob=blob_name)  # type: ignore[attr-defined]
                blob_client.upload_blob(data, overwrite=True, content_settings=_ContentSettings(content_type=content_type))
                return blob_client.url

            try:
                # [FIX-CREATE-SAVE] Verificar tamaño > 0 en storage
                ffield = getattr(document, 'file', None)
                try:
                    if ffield and getattr(ffield, 'storage', None) and getattr(ffield, 'name', None):
                        size_on_storage = ffield.storage.size(ffield.name)
                        if not size_on_storage:
                            raise ValueError('[FIX-CREATE-SAVE] Archivo guardado con tamaño 0 en storage')
                except Exception as _size_exc:
                    logger.error(f"[FIX-CREATE-SAVE] Verificación tamaño falló: {_size_exc}")
                    raise

                # [FIX-CREATE-OCR] Reabrir desde storage y validar/normalizar imagen
                from io import BytesIO as _BytesIO
                stable_bytes = b''
                try:
                    storage_backend = ffield.storage  # type: ignore[assignment]
                    with storage_backend.open(ffield.name, 'rb') as fh:  # type: ignore[call-arg]
                        try:
                            fh.seek(0)
                        except Exception:
                            pass
                        stable_bytes = fh.read()
                except Exception as _open_exc:
                    logger.warning(f"[FIX-CREATE-OCR] No se pudo reabrir desde storage; se intentará con upload directo: {_open_exc}")
                    try:
                        if hasattr(uploaded_file, 'seek'):
                            try:
                                uploaded_file.seek(0)
                            except Exception:
                                pass
                        stable_bytes = uploaded_file.read()
                    except Exception:
                        stable_bytes = b''

                try:
                    from PIL import Image as _Image  # type: ignore
                    _Image.open(_BytesIO(stable_bytes)).verify()
                    _img = _Image.open(_BytesIO(stable_bytes)).convert('RGB')
                    _buf = _BytesIO()
                    _img.save(_buf, format='JPEG')
                    jpeg_bytes = _buf.getvalue()
                except Exception as _pil_exc:
                    logger.warning(f"[FIX-CREATE-OCR] PIL.verify() falló; usando bytes crudos: {_pil_exc}")
                    jpeg_bytes = stable_bytes

                # 1) Subir JPG fijo por ID con bytes normalizados
                jpg_blob_name = f"documents/{document.id}.jpg"
                _upload_blob_overwrite('vea-connect-files', jpg_blob_name, jpeg_bytes, 'image/jpeg')

                # 2) Ejecutar OCR desde bytes normalizados
                ocr_text = ''
                try:
                    content_file = ContentFile(jpeg_bytes, name=f"{document.id}.jpg")
                    extracted = convert_document_to_text(content_file)
                    if isinstance(extracted, str) and not extracted.startswith('Error al extraer contenido'):
                        ocr_text = extracted
                except Exception as ocr_exc:
                    logger.warning(f"[FIX-CREATE-OCR] OCR falló; se continúa con título/descripcion: {ocr_exc}")
                    ocr_text = ''

                # 3) TXT base y subida {id}.txt
                title = form.cleaned_data.get('title', '')
                description = form.cleaned_data.get('description', '')
                category = form.cleaned_data.get('category', '')
                embedding_text = "\n".join([str(title or ''), str(description or ''), str(ocr_text or '')]).strip()

                txt_blob_name = f"{document.id}.txt"
                _upload_blob_overwrite('vea-connect-files', txt_blob_name, embedding_text.encode('utf-8'), 'text/plain; charset=utf-8')

                # 4) Embeddings y upsert
                vector = generate_embeddings(embedding_text)
                document_vector_id = f"doc_{document.id}"

                created_dt = document.date or timezone.now()
                if timezone.is_naive(created_dt):
                    try:
                        created_dt = timezone.make_aware(created_dt, timezone=timezone.utc)  # type: ignore[arg-type]
                    except Exception:
                        created_dt = timezone.now()
                created_at_iso = created_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

                metadata = {
                    'title': title,
                    'created_at': created_at_iso,
                    'metadata': json.dumps({
                        'category': category,
                        'description': description,
                        'filename': f"documents/{document.id}.jpg",
                        'ocr_text': ocr_text or ''
                    })
                }
                if isinstance(vector, list) and vector:
                    metadata['embedding'] = vector
                search_index_service.upsert_document(document_vector_id, embedding_text, metadata)

                # 5) Actualizar y guardar
                document.title = title
                document.description = description
                document.category = category
                document.file.name = jpg_blob_name
                document.file_type = 'jpg'
                document.processing_state = ProcessingState.READY
                document.is_processed = True
                document.user = request.user
                document.save()

                messages.success(request, f"El documento '{document.title}' se creó correctamente.")
                return redirect('documents:document_list')
            except Exception as err2:
                logger.error(f"Error en CREATE al subir/indizar: {err2}")
                messages.error(request, "Error al subir o procesar el documento. Intenta nuevamente.")
                return render(request, 'documents/create.html', {'form': form})
        else:
            return render(request, 'documents/create.html', {'form': form})
    else:
        form = DocumentForm()
    return render(request, 'documents/create.html', {'form': form})


@login_required
def document_list(request):
    try:
        # Filtrar solo documentos válidos (con título y archivo)
        documents = Document.objects.filter(
            title__isnull=False,
            title__gt='',  # Título no vacío
            file__isnull=False,
            file__gt=''    # Archivo no vacío
        ).exclude(
            title='',      # Excluir títulos vacíos
            description='' # Excluir descripciones vacías
        )

        # Log temporal para depuración
        logger.warning(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', None)}")
        if documents:
            logger.warning(f"Primer doc file.url: {getattr(documents[0].file, 'url', None)}")
    except Exception as e:
        logger.error(f"Error al obtener documentos: {e}")
        # Si hay error de migración, mostrar mensaje y documentos vacíos
        if "vector_id" in str(e):
            messages.error(request, "El sistema está siendo actualizado. Por favor, intenta nuevamente en unos minutos.")
        documents = Document.objects.none()

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')

    if q and documents:
        search_filters = reduce(operator.or_, [
            Q(title__icontains=q),
            Q(description__icontains=q),
            Q(category__icontains=q),
            Q(date__icontains=q)
        ])
        documents = documents.filter(search_filters)
    if category and documents:
        documents = documents.filter(category=category)

    # Obtener las categorías del modelo
    category_choices = Document.CATEGORY_CHOICES

    return render(request, 'documents.html', {
        'documents': documents,
        'q': q,
        'selected_category': category,
        'category_choices': category_choices,
        'messages': messages.get_messages(request),
    })


@login_required
def edit_document(request, pk):
    # DEBUG EDIT: edit_document llamado con pk={pk}
    # DEBUG EDIT: request.method = {request.method}

    # Permitir que administradores/staff editen cualquier documento.
    if request.user.is_superuser or request.user.is_staff:
        document = get_object_or_404(Document, pk=pk)
    else:
        # Permitir que usuarios autenticados editen documentos sin usuario asignado o sus propios documentos
        try:
            document = get_object_or_404(Document, pk=pk, user=request.user)
        except Exception:
            # Si no es su documento, verificar si es un documento sin usuario asignado
            document = get_object_or_404(Document, pk=pk, user__isnull=True)

    # DEBUG EDIT: document encontrado: {document}

    if request.method == 'POST':
        # DEBUG EDIT: request.FILES = {request.FILES}
        # DEBUG EDIT: request.FILES.keys() = {list(request.FILES.keys())}

        form = DocumentForm(request.POST, request.FILES, instance=document)
        # DEBUG EDIT: form.is_valid() = {form.is_valid()}
        if not form.is_valid():
            # DEBUG EDIT: form.errors = {form.errors}
            pass
        if form.is_valid():
            # Helper local: subida explícita con overwrite y nombre exacto
            def _upload_blob_overwrite(container: str, blob_name: str, data: bytes, content_type: str) -> str:
                if not azure_storage or not getattr(azure_storage, 'client', None):
                    raise Exception('Azure Storage client no disponible')
                from azure.storage.blob import ContentSettings as _ContentSettings
                blob_client = azure_storage.client.get_blob_client(container=container, blob=blob_name)  # type: ignore[attr-defined]
                blob_client.upload_blob(data, overwrite=True, content_settings=_ContentSettings(content_type=content_type))
                return blob_client.url

            # Capturar archivo y preparar campos del formulario
            new_file = request.FILES.get('file', None)
            # DEBUG EDIT: new_file from request.FILES = {new_file}
            # DEBUG EDIT: type(new_file) = {type(new_file)}

            form_data = form.cleaned_data
            new_title = form_data.get('title', document.title)
            new_description = form_data.get('description', document.description)
            new_category = form_data.get('category', document.category)

            # Variables de resultado
            ocr_text = ""

            # [FIX-EDIT-OCR] Si llega archivo nuevo en EDIT, guardar primero en storage y luego OCR
            if new_file:
                # 1) Rebobinar por si algún validador leyó el stream
                if hasattr(new_file, 'seek'):
                    try:
                        new_file.seek(0)
                    except Exception:
                        pass

                # 2) Asignar el upload ORIGINAL al FileField del instance (sin .read())
                try:
                    document.file = new_file  # type: ignore[assignment]
                except Exception as _assign_exc:
                    logger.warning(f"[FIX-EDIT-OCR] No se pudo asignar upload al FileField: {_assign_exc}")

                # 3) Guardar primero el modelo para persistir el archivo en storage
                document.save()

                # 4) Refrescar por si signals cambian nombre/ruta
                try:
                    document.refresh_from_db()
                except Exception:
                    pass

                # 5) Verificar tamaño en storage > 0 (defensivo)
                ffield = getattr(document, 'file', None)
                try:
                    if ffield and getattr(ffield, 'storage', None) and getattr(ffield, 'name', None):
                        size_on_storage = ffield.storage.size(ffield.name)
                        if not size_on_storage or size_on_storage == 0:
                            raise ValueError('[FIX-EDIT-OCR] Archivo guardado con tamaño 0 en storage')
                except Exception as _size_exc:
                    logger.error(f"[FIX-EDIT-OCR] Verificación tamaño falló: {_size_exc}")
                    raise

                # 6) Reabrir DESDE storage y hacer OCR + embeddings (idéntico a CREATE)
                stable_bytes = b''
                try:
                    storage_backend = ffield.storage  # type: ignore[assignment]
                    with storage_backend.open(ffield.name, 'rb') as fh:  # type: ignore[call-arg]
                        try:
                            fh.seek(0)
                        except Exception:
                            pass
                        stable_bytes = fh.read()
                except Exception as _open_exc:
                    logger.warning(f"[FIX-EDIT-OCR] No se pudo reabrir desde storage: {_open_exc}")
                    stable_bytes = b''

                # Validar/normalizar imagen con PIL y subir a Azure Blob
                from io import BytesIO as _BytesIO
                try:
                    from PIL import Image as _Image  # type: ignore
                    _Image.open(_BytesIO(stable_bytes)).verify()
                    _img = _Image.open(_BytesIO(stable_bytes)).convert('RGB')
                    _buf = _BytesIO()
                    _img.save(_buf, format='JPEG')
                    jpeg_bytes = _buf.getvalue()
                except Exception as _pil_exc:
                    logger.warning(f"[FIX-EDIT-OCR] PIL.verify() falló; usando bytes crudos: {_pil_exc}")
                    jpeg_bytes = stable_bytes

                # Subir imagen como documents/{id}.jpg con bytes normalizados
                jpg_blob_name = f"documents/{document.id}.jpg"
                _upload_blob_overwrite('vea-connect-files', jpg_blob_name, jpeg_bytes, 'image/jpeg')

                # Actualizar campos de archivo en el modelo (sin disparar pipeline)
                document.file.name = jpg_blob_name
                document.file_type = 'jpg'

                # Ejecutar OCR usando los bytes normalizados
                try:
                    content_file = ContentFile(jpeg_bytes, name=f"{document.id}.jpg")
                    ocr_text = convert_document_to_text(content_file)
                except Exception as _ocr_exc:
                    logger.warning(f"[FIX-EDIT-OCR] OCR falló: {_ocr_exc}")
                    ocr_text = ""

            # [EDIT-NOFILE-OCR-AZURE] Si NO se sube nueva imagen, leer desde Azure Blob y extraer OCR
            if not new_file and (ocr_text is None or ocr_text == ""):
                try:
                    if not getattr(azure_storage, 'client', None):
                        logger.warning("[EDIT-NOFILE-OCR-AZURE] Azure Storage client no disponible")
                        raise Exception("Azure client unavailable")

                    container = 'vea-connect-files'
                    blob_name = f"documents/{document.id}.jpg"

                    # Intento 1: descargar blob esperado por ID
                    blob_client = azure_storage.client.get_blob_client(container=container, blob=blob_name)  # type: ignore[attr-defined]
                    try:
                        blob_bytes = blob_client.download_blob().readall()
                    except Exception as _dl_exc:
                        logger.warning(f"[EDIT-NOFILE-OCR-AZURE] No se pudo descargar {blob_name}: {_dl_exc}")
                        # Intento 2: resolver nombre alterno usando helper existente
                        alt_name = None
                        try:
                            alt_name = _find_azure_blob(document)
                        except Exception as _find_exc:
                            logger.warning(f"[EDIT-NOFILE-OCR-AZURE] _find_azure_blob falló: {_find_exc}")
                        if not alt_name:
                            raise
                        blob_client = azure_storage.client.get_blob_client(container=container, blob=alt_name)  # type: ignore[attr-defined]
                        blob_bytes = blob_client.download_blob().readall()

                    # Normalizar a JPEG para OCR (idéntico criterio que en CREATE/EDIT con archivo nuevo)
                    from io import BytesIO as _BytesIO
                    try:
                        from PIL import Image as _Image  # type: ignore
                        _Image.open(_BytesIO(blob_bytes)).verify()
                        _img = _Image.open(_BytesIO(blob_bytes)).convert('RGB')
                        _buf = _BytesIO()
                        _img.save(_buf, format='JPEG')
                        jpeg_bytes = _buf.getvalue()
                    except Exception as _pil_exc:
                        logger.warning(f"[EDIT-NOFILE-OCR-AZURE] PIL.verify() falló; usando bytes crudos: {_pil_exc}")
                        jpeg_bytes = blob_bytes

                    # Ejecutar OCR con bytes desde Azure Blob
                    try:
                        content_file = ContentFile(jpeg_bytes, name=f"{document.id}.jpg")
                        ocr_text = convert_document_to_text(content_file)
                    except Exception as _ocr_exc:
                        logger.warning(f"[EDIT-NOFILE-OCR-AZURE] OCR falló: {_ocr_exc}")
                        ocr_text = ""
                except Exception as _exc:
                    logger.warning(f"[EDIT-NOFILE-OCR-AZURE] No se pudo extraer OCR desde Azure: {_exc}")
                    ocr_text = ocr_text or ""

            # Construir texto para embeddings y TXT
            embedding_text = "\n".join([str(new_title or ''), str(new_description or ''), str(ocr_text or '')]).strip()

            # Subir TXT como {id}.txt en la raíz del contenedor
            txt_blob_name = f"{document.id}.txt"
            _upload_blob_overwrite('vea-connect-files', txt_blob_name, embedding_text.encode('utf-8'), 'text/plain; charset=utf-8')

            # Generar embeddings y upsert en Azure Search con key estable
            vector = generate_embeddings(embedding_text)
            document_vector_id = f"doc_{document.id}"

            created_dt = document.date or timezone.now()
            if timezone.is_naive(created_dt):
                try:
                    created_dt = timezone.make_aware(created_dt, timezone=timezone.utc)  # type: ignore[arg-type]
                except Exception:
                    created_dt = timezone.now()
            created_at_iso = created_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

            metadata = {
                'title': new_title,
                'created_at': created_at_iso,
                'metadata': json.dumps({
                    'category': new_category,
                    'description': new_description,
                    'filename': getattr(getattr(document, 'file', None), 'name', None),
                    'ocr_text': ocr_text or ''
                })
            }
            if isinstance(vector, list) and vector:
                metadata['embedding'] = vector
            search_index_service.upsert_document(document_vector_id, embedding_text, metadata)

            # Actualizar campos del documento sin marcar PENDING
            document.title = new_title
            document.description = new_description
            document.category = new_category
            document.user = request.user
            if not getattr(document, 'date', None):
                document.date = datetime.datetime.now()
            document.processing_state = ProcessingState.READY
            document.is_processed = True
            document.save()

            messages.success(request, 'Documento actualizado correctamente.')
            return redirect('documents:document_list')
    else:
        form = DocumentForm(instance=document)
    return render(request, 'documents/create.html', {'form': form, 'edit': True})


@login_required
def delete_document(request, pk):
    # Permitir que administradores/staff eliminen cualquier documento.
    if request.user.is_superuser or request.user.is_staff:
        document = get_object_or_404(Document, pk=pk)
    else:
        # Permitir que usuarios autenticados eliminen documentos sin usuario asignado o sus propios documentos
        try:
            document = get_object_or_404(Document, pk=pk, user=request.user)
        except Exception:
            # Si no es su documento, verificar si es un documento sin usuario asignado
            document = get_object_or_404(Document, pk=pk, user__isnull=True)
    if request.method == 'POST':
        try:
            # 1) Borrar blobs por ID fijo
            img_blob = f"documents/{document.id}.jpg"
            txt_blob = f"{document.id}.txt"
            container = 'vea-connect-files'
            img_deleted = False
            txt_deleted = False
            try:
                # Asegurar cliente
                if not getattr(azure_storage, 'client', None):
                    try:
                        getattr(azure_storage, '_ensure_client', lambda: False)()
                    except Exception:
                        pass
                client = getattr(azure_storage, 'client', None)
                if client is not None:
                    blob_client_img = client.get_blob_client(container=container, blob=img_blob)
                    try:
                        blob_client_img.delete_blob(delete_snapshots='include')
                        img_deleted = True
                        logger.info(f"Blob eliminado: {container}/{img_blob}")
                    except Exception as _e_img:
                        logger.warning(f"No se pudo eliminar blob (posible inexistente): {container}/{img_blob} -> {_e_img}")
                    blob_client_txt = client.get_blob_client(container=container, blob=txt_blob)
                    try:
                        blob_client_txt.delete_blob(delete_snapshots='include')
                        txt_deleted = True
                        logger.info(f"Blob eliminado: {container}/{txt_blob}")
                    except Exception as _e_txt:
                        logger.warning(f"No se pudo eliminar blob (posible inexistente): {container}/{txt_blob} -> {_e_txt}")
                else:
                    logger.warning("Azure Storage client no disponible para eliminar blobs por ID")
            except Exception as _e:
                logger.warning(f"Fallo general al eliminar blobs por ID: {_e}")

            # 2) Eliminar en Azure Search por la misma key usada en indexación
            try:
                from services.search_index_service import search_index_service as _sis
                if _sis.client:
                    search_key = f"doc_{document.id}"
                    deleted = _sis.delete_document(search_key)
                    if deleted:
                        logger.info(f"Documento eliminado de Azure AI Search: {search_key}")
                    else:
                        logger.warning(f"No se encontró en Azure AI Search (key): {search_key}")
                else:
                    logger.warning("Azure AI Search client no disponible para eliminar por key")
            except Exception as e:
                logger.warning(f"No se pudo eliminar de Azure AI Search: {e}")

            # 3) Eliminar el documento de la base de datos
            try:
                document.delete()
            except Exception as e:
                logger.error(f"Error eliminando registro en BD para documento {document.id}: {e}")
                messages.error(request, 'Error al eliminar el registro en base de datos.')
                return redirect('documents:document_list')

            # Mensajes finales
            if img_deleted or txt_deleted:
                messages.success(request, 'Documento eliminado de storage (por ID) y de la base de datos.')
            else:
                messages.warning(request, 'Documento eliminado de la base de datos. No se encontraron blobs por ID para borrar.')

        except Exception as e:
            logger.error(f"Error eliminando documento {getattr(document, 'title', pk)}: {str(e)}")
            messages.error(request, 'Error al eliminar el documento. Por favor, intenta nuevamente.')

        return redirect('documents:document_list')
    return render(request, 'documents/confirm_delete.html', {'document': document})


@login_required
def download_document(request, pk):
    """
    Descarga un documento con soporte para Azure Blob Storage y FileSystemStorage.

    Args:
        request: HttpRequest object
        pk: Primary key del documento

    Returns:
        HttpResponse: FileResponse para archivos locales o redirect para Azure
        JsonResponse: En caso de error con detalles específicos
    """
    logger.info(f"Iniciando descarga del documento con pk: {pk}")

    try:
        # Buscar el documento por pk
        document = get_object_or_404(Document, pk=pk)
        logger.info(f"Documento encontrado: {document.title} (ID: {document.pk})")

        # Validar que el documento tenga archivo asociado
        if not document.file or not document.file.name:
            logger.error(f"Documento {document.title} no tiene archivo asociado")
            return JsonResponse({
                'error': 'Documento no encontrado',
                'message': f"El documento '{document.title}' no tiene un archivo asociado.",
                'document_id': pk
            }, status=404)

        # Preferir Azure Blob Storage si el cliente está inicializado,
        # independientemente del valor de DEFAULT_FILE_STORAGE. Esto evita
        # depender del backend de archivos y es no disruptivo.
        try:
            if azure_storage and getattr(azure_storage, 'client', None):
                logger.info(f"Azure Storage client disponible. Usando Azure para: {document.title}")
                return _handle_azure_download(document)
        except Exception as _e:
            logger.warning(f"No se pudo usar Azure Storage directamente: {_e}")

        # Detectar el tipo de storage configurado (fallback informativo)
        default_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', '')
        is_file_system_storage = 'FileSystemStorage' in default_storage
        logger.info(f"Tipo de storage detectado: {default_storage}")
        logger.info(f"¿Es FileSystemStorage?: {is_file_system_storage}")

        # Manejar FileSystemStorage si está explícitamente configurado
        if is_file_system_storage:
            logger.info(f"Procesando descarga desde FileSystemStorage para: {document.title}")
            return _handle_filesystem_download(document)

        # Fallback: intentar detectar automáticamente
        else:
            logger.warning(f"Tipo de storage no reconocido: {default_storage}, intentando detección automática")
            return _handle_automatic_download(document)

    except Document.DoesNotExist:
        logger.error(f"Documento con pk {pk} no encontrado en la base de datos")
        return JsonResponse({
            'error': 'Documento no encontrado',
            'message': 'El documento especificado no existe en la base de datos.',
            'document_id': pk
        }, status=404)

    except Exception as e:
        logger.exception(f"Error inesperado durante la descarga del documento {pk}: {str(e)}")
        return JsonResponse({
            'error': 'Error interno del servidor',
            'message': 'Ocurrió un error inesperado durante la descarga. Por favor, intenta nuevamente.',
            'document_id': pk
        }, status=500)


def _handle_azure_download(document):
    """
    Maneja la descarga desde Azure Blob Storage.

    Args:
        document: Document object

    Returns:
        HttpResponse: Redirect a URL firmada o JsonResponse con error
    """
    logger.info(f"Procesando descarga Azure para documento: {document.title}")

    try:
        # Validar que el servicio de Azure esté disponible
        if not azure_storage or not azure_storage.client:
            logger.error("Servicio de Azure Storage no disponible")
            return JsonResponse({
                'error': 'Servicio de almacenamiento no disponible',
                'message': 'El servicio de Azure Storage no está configurado correctamente.',
                'document_id': document.pk
            }, status=503)

        # Buscar el archivo en Azure con diferentes estrategias
        found_filename = _find_azure_blob(document)

        if not found_filename:
            logger.error(f"Archivo no encontrado en Azure Storage para: {document.title}")
            return JsonResponse({
                'error': 'Archivo no encontrado',
                'message': f"El archivo '{document.title}' no se encuentra en el almacenamiento de Azure.",
                'document_id': document.pk,
                'suggestions': [
                    'Verifica que el archivo fue subido correctamente',
                    'Contacta al administrador si el problema persiste'
                ]
            }, status=404)

        # Generar URL firmada para descarga
        logger.info(f"Generando URL firmada para: {found_filename}")
        url_result = azure_storage.get_blob_url(found_filename, expires_in=3600)  # 1 hora de expiración

        if not url_result.get('success'):
            # Fallback: intentar resolver por nombre directo y reintentar
            try:
                logger.warning("Fallo primera generación de SAS; intentando resolución directa del blob")
                resolved = azure_storage.resolve_blob_name(document.file.name)
            except Exception as _e:
                resolved = None

            if resolved:
                logger.info(f"Reintentando con nombre resuelto: {resolved}")
                url_result = azure_storage.get_blob_url(resolved, expires_in=3600)

            if not url_result.get('success'):
                logger.error(f"Error generando URL firmada: {url_result.get('error')}")
                return JsonResponse({
                    'error': 'Error generando URL de descarga',
                    'message': 'No se pudo generar la URL de descarga. Por favor, intenta nuevamente.',
                    'document_id': document.pk
                }, status=500)

        download_url = url_result.get('signed_url')
        if not download_url:
            logger.error(f"signed_url no disponible para: {found_filename}")
            return JsonResponse({
                'error': 'Error generando URL de descarga',
                'message': 'La URL firmada no fue generada por el storage.',
                'document_id': document.pk
            }, status=500)

        logger.info(f"URL de descarga generada exitosamente para: {found_filename}")
        logger.info(f"URL final: {str(download_url)[:100]}...")  # Log parcial de la URL

        # Redirigir a la URL firmada
        return redirect(download_url)

    except Exception as e:
        logger.exception(f"Error durante descarga Azure para {document.title}: {str(e)}")
        return JsonResponse({
            'error': 'Error en descarga Azure',
            'message': f'Ocurrió un error durante la descarga desde Azure Storage: {str(e)}',
            'document_id': document.pk
        }, status=500)


def _handle_filesystem_download(document):
    """
    Maneja la descarga desde FileSystemStorage.

    Args:
        document: Document object

    Returns:
        FileResponse: Respuesta con el archivo o JsonResponse con error
    """
    logger.info(f"Procesando descarga FileSystem para documento: {document.title}")

    try:
        # Obtener la ruta completa del archivo
        file_path = document.file.path
        logger.info(f"Ruta del archivo: {file_path}")

        # Validar que el archivo existe físicamente
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado en sistema de archivos: {file_path}")
            return JsonResponse({
                'error': 'Archivo no encontrado',
                'message': f"El archivo '{document.title}' no se encuentra en el sistema de archivos.",
                'document_id': document.pk,
                'file_path': file_path
            }, status=404)

        # Validar que es un archivo (no directorio)
        if not os.path.isfile(file_path):
            logger.error(f"La ruta no es un archivo válido: {file_path}")
            return JsonResponse({
                'error': 'Ruta inválida',
                'message': 'La ruta especificada no corresponde a un archivo válido.',
                'document_id': document.pk
            }, status=400)

        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        logger.info(f"Tamaño del archivo: {file_size} bytes")

        # Determinar el tipo MIME
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        logger.info(f"Tipo de contenido detectado: {content_type}")

        # Crear nombre de archivo para descarga
        filename = os.path.basename(file_path)
        if not filename:
            filename = f"{document.title}.{document.file_type}" if document.file_type else "documento"

        logger.info(f"Nombre de archivo para descarga: {filename}")

        # Abrir archivo en modo binario y streaming
        try:
            file_handle = open(file_path, 'rb')
            logger.info(f"Archivo abierto exitosamente para streaming: {file_path}")
        except IOError as e:
            logger.error(f"Error abriendo archivo {file_path}: {str(e)}")
            return JsonResponse({
                'error': 'Error de acceso al archivo',
                'message': 'No se pudo acceder al archivo. Verifica permisos.',
                'document_id': document.pk
            }, status=500)

        # Crear FileResponse con streaming
        response = FileResponse(
            file_handle,
            content_type=content_type,
            as_attachment=True,
            filename=filename
        )

        # Agregar headers adicionales
        response['Content-Length'] = file_size
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        logger.info(f"FileResponse creado exitosamente para: {filename}")
        logger.info(f"Headers de respuesta: Content-Type={content_type}, Content-Length={file_size}")

        return response

    except Exception as e:
        logger.exception(f"Error durante descarga FileSystem para {document.title}: {str(e)}")
        return JsonResponse({
            'error': 'Error en descarga FileSystem',
            'message': f'Ocurrió un error durante la descarga del archivo: {str(e)}',
            'document_id': document.pk
        }, status=500)


def _handle_automatic_download(document):
    """
    Maneja la descarga con detección automática del tipo de storage.

    Args:
        document: Document object

    Returns:
        HttpResponse: Respuesta apropiada según el storage detectado
    """
    logger.info(f"Intentando detección automática de storage para: {document.title}")

    try:
        # Intentar primero con Azure Storage
        if azure_storage and azure_storage.client:
            logger.info("Azure Storage disponible, intentando descarga Azure")
            return _handle_azure_download(document)

        # Si no hay Azure, intentar con FileSystem
        logger.info("Azure Storage no disponible, intentando descarga FileSystem")
        return _handle_filesystem_download(document)

    except Exception as e:
        logger.exception(f"Error en detección automática para {document.title}: {str(e)}")
        return JsonResponse({
            'error': 'Error de detección de storage',
            'message': 'No se pudo determinar el tipo de almacenamiento del archivo.',
            'document_id': document.pk
        }, status=500)


def _find_azure_blob(document):
    """
    Busca un blob en Azure Storage usando múltiples estrategias.

    Args:
        document: Document object

    Returns:
        str: Nombre del blob encontrado o None si no se encuentra
    """
    logger.info(f"Buscando blob en Azure para: {document.title}")

    # Lista de nombres posibles para buscar
    possible_filenames = [
        document.file.name,  # Nombre actual en la base de datos
        f"documents/{document.file.name}",  # Con prefijo documents/
        f"documents/{document.title}.{document.file_type}" if document.file_type else None,  # Basado en título
    ]

    # Filtrar nombres None
    possible_filenames = [f for f in possible_filenames if f]
    logger.info(f"Nombres posibles a buscar: {possible_filenames}")

    # Estrategia 1: Buscar con nombres exactos
    logger.info("Buscando con nombres exactos")
    for filename in possible_filenames:
        logger.info(f"Verificando existencia de: {filename}")
        exists_result = azure_storage.blob_exists(filename)
        if exists_result.get('success') and exists_result.get('exists'):
            logger.info(f"Archivo encontrado en storage: {filename}")
            return filename

    # Estrategia 2: Limpiar nombres con doble prefijo y buscar
    logger.info("Limpiando nombres con doble prefijo")
    for filename in possible_filenames:
        # Remover doble prefijo documents/documents/
        if filename.startswith('documents/documents/'):
            clean_name = filename[len('documents/'):]
            logger.info(f"Buscando nombre limpio: {clean_name}")
            exists_result = azure_storage.blob_exists(clean_name)
            if exists_result.get('success') and exists_result.get('exists'):
                logger.info(f"Archivo encontrado con nombre limpio: {clean_name}")
                return clean_name

    # Estrategia 3: Buscar por hash del archivo (últimos 6 caracteres del nombre)
    logger.info("Buscando por hash del archivo")
    if document.file.name:
        base_name = os.path.basename(document.file.name)
        name_parts = base_name.split('_')
        if len(name_parts) >= 2:
            hash_part = name_parts[-1].split('.')[0]  # Última parte antes de la extensión
            logger.info(f"Buscando por hash: {hash_part}")

            # Buscar archivos que contengan este hash
            all_blobs_result = azure_storage.list_blobs()
            if all_blobs_result.get('success') and all_blobs_result.get('blobs'):
                all_blobs = all_blobs_result.get('blobs', [])

                # Priorizar archivos originales (imágenes, PDFs) sobre archivos convertidos (.txt)
                original_files = []
                converted_files = []

                for blob in all_blobs:
                    blob_name = blob.get('name', '')
                    if hash_part in blob_name:
                        if blob_name.endswith(('.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx')):
                            original_files.append(blob_name)
                        elif blob_name.endswith('.txt') and 'converted' in blob_name:
                            converted_files.append(blob_name)

                # Devolver archivo original si existe, sino archivo convertido
                if original_files:
                    logger.info(f"Archivo original encontrado por hash: {original_files[0]}")
                    return original_files[0]
                elif converted_files:
                    logger.info(f"Archivo convertido encontrado por hash: {converted_files[0]}")
                    return converted_files[0]

    # Estrategia 4: Buscar por patrón del título
    if document.title:
        logger.info(f"Buscando por patrón de título: {document.title}")

        # Buscar archivos que contengan palabras del título
        title_words = document.title.lower().split()
        all_blobs_result = azure_storage.list_blobs()
        if all_blobs_result.get('success') and all_blobs_result.get('blobs'):
            all_blobs = all_blobs_result.get('blobs', [])

            # Separar archivos originales y convertidos
            original_matches = []
            converted_matches = []

            # Buscar archivos que contengan todas las palabras del título
            for blob in all_blobs:
                blob_name = blob.get('name', '').lower()
                if all(word in blob_name for word in title_words if len(word) > 2):
                    if blob_name.endswith(('.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx')):
                        original_matches.append(blob.get('name'))
                    elif blob_name.endswith('.txt') and 'converted' in blob_name:
                        converted_matches.append(blob.get('name'))

            # Priorizar archivos originales
            if original_matches:
                logger.info(f"Archivo original encontrado por patrón de título: {original_matches[0]}")
                return original_matches[0]
            elif converted_matches:
                logger.info(f"Archivo convertido encontrado por patrón de título: {converted_matches[0]}")
                return converted_matches[0]

            # Si no encuentra con todas las palabras, buscar con al menos una palabra importante
            original_matches = []
            converted_matches = []

            for blob in all_blobs:
                blob_name = blob.get('name', '').lower()
                important_words = [word for word in title_words if len(word) > 3]
                if important_words and any(word in blob_name for word in important_words):
                    if blob_name.endswith(('.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx')):
                        original_matches.append(blob.get('name'))
                    elif blob_name.endswith('.txt') and 'converted' in blob_name:
                        converted_matches.append(blob.get('name'))

            # Priorizar archivos originales
            if original_matches:
                logger.info(f"Archivo original encontrado por palabra importante: {original_matches[0]}")
                return original_matches[0]
            elif converted_matches:
                logger.info(f"Archivo convertido encontrado por palabra importante: {converted_matches[0]}")
                return converted_matches[0]

    # Estrategia 5: Búsqueda amplia por contenido del título
    logger.info("Realizando búsqueda amplia por contenido del título")
    if document.title:
        all_blobs_result = azure_storage.list_blobs()
        if all_blobs_result.get('success') and all_blobs_result.get('blobs'):
            all_blobs = all_blobs_result.get('blobs', [])

            # Separar archivos originales y convertidos
            original_matches = []
            converted_matches = []

            for blob in all_blobs:
                blob_name = blob.get('name', '')
                if document.title.lower() in blob_name.lower():
                    if blob_name.endswith(('.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx')):
                        original_matches.append(blob_name)
                    elif blob_name.endswith('.txt') and 'converted' in blob_name:
                        converted_matches.append(blob_name)

            # Priorizar archivos originales
            if original_matches:
                logger.info(f"Archivo original encontrado por búsqueda amplia: {original_matches[0]}")
                return original_matches[0]
            elif converted_matches:
                logger.info(f"Archivo convertido encontrado por búsqueda amplia: {converted_matches[0]}")
                return converted_matches[0]

    logger.warning(f"No se encontró el archivo en Azure Storage para: {document.title}")
    return None
