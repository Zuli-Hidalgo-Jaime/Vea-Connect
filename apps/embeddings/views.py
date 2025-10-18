import logging
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseServerError
from utilities.embedding_manager import EmbeddingManager, EmbeddingServiceUnavailable

logger = logging.getLogger(__name__)

# Instancia global del manager (puede inyectarse en tests)
def get_manager(request=None):
    # Permite inyección de manager mockeado en tests
    if request and hasattr(request, '_manager'):
        return request._manager
    try:
        return EmbeddingManager()
    except EmbeddingServiceUnavailable as e:
        logger.error(f"AI Search no disponible: {e}")
        return None

def create_embedding(request):
    manager = get_manager()
    if not manager:
        return HttpResponse(content=b"Azure AI Search no disponible", content_type="text/plain", status=503)
    if request.method == 'POST':
        document_id = request.POST.get('document_id')
        content = request.POST.get('content') or request.POST.get('text')
        metadata = request.POST.get('metadata', '{}')
        if document_id and content:
            try:
                embedding = manager.create_embedding(document_id=document_id, content=content)
                if embedding and embedding.get('status') == 'success':
                    return JsonResponse({'status': 'success'}, status=201)
                return JsonResponse({'status': 'error', 'message': embedding.get('message', 'Error')}, status=400)
            except Exception as e:
                logger.error(f"Error creando embedding: {e}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return render(request, 'embeddings/create.html')

def list_embeddings(request):
    manager = get_manager(request)
    if not manager:
        return HttpResponse(content=b"Azure AI Search no disponible", content_type="text/plain", status=503)
    try:
        result = manager.list_embeddings()
        embeddings = result.get('data', {}).get('embeddings', [])
    except Exception as e:
        logger.error(f"Error listando embeddings: {e}")
        embeddings = []
    return render(request, 'embeddings/list.html', {'embeddings': embeddings})

def delete_embedding(request, pk):
    manager = get_manager()
    if not manager:
        return HttpResponse(content=b"Azure AI Search no disponible", content_type="text/plain", status=503)
    if request.method == 'POST':
        try:
            result = manager.delete_embedding(str(pk))
            if result and result.get('status') == 'success':
                return JsonResponse({'status': 'success'}, status=200)
            return JsonResponse({'status': 'error', 'message': result.get('message', 'Error')}, status=400)
        except Exception as e:
            logger.error(f"Error eliminando embedding: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return render(request, 'embeddings/confirm_delete.html', {'pk': pk})

def bulk_upload(request):
    manager = get_manager()
    if not manager:
        return HttpResponse(content=b"Azure AI Search no disponible", content_type="text/plain", status=503)
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            try:
                import csv
                import io
                content = uploaded_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(content))
                for row in csv_reader:
                    text = row.get('text', '')
                    category = row.get('category', '')
                    if text:
                        metadata = {'category': category}
                        manager.create_embedding(
                            document_id=f"bulk_{datetime.utcnow().timestamp()}",
                            content=text,
                            metadata=metadata
                        )
                return JsonResponse({'status': 'success'}, status=201)
            except Exception as e:
                logger.error(f"Error en bulk upload: {e}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return render(request, 'embeddings/bulk_upload.html') 