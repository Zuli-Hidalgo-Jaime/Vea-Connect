import os
import tempfile
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from utilities.azureblobstorage import save_extracted_text_to_blob

from .azure_vision_service import AzureVisionService

logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def extract_text_from_file(request):
    """
    Extract text from uploaded image or PDF file.
    
    This view accepts file uploads and uses Azure Computer Vision
    to extract text from images or PDF documents.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        JsonResponse: JSON response with extracted text or error message
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Validate file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File size too large. Maximum size is 10MB.'
            }, status=400)
        
        # Validate file type
        allowed_extensions = {
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.pdf'
        }
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported file type: {file_extension}. '
                        f'Supported types: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Initialize Azure Vision Service
            vision_service = AzureVisionService()
            
            # Extract text based on file type
            # Aquí se almacena el resultado del procesamiento de Vision, se mantiene documentado para posibles ajustes de integración con AI Search.
            if file_extension == '.pdf':
                extracted_text = vision_service.extract_text_from_pdf(temp_file_path)
            else:
                extracted_text = vision_service.extract_text_from_image(temp_file_path)
            
            # Se agrega almacenamiento del texto extraído por Azure Computer Vision en la carpeta converted/ para futura indexación en Azure AI Search
            # Save extracted text to blob storage for future indexing
            metadata = {
                "file_type": file_extension,
                "original_filename": uploaded_file.name,
                "extraction_method": "azure_computer_vision",
                "user_id": request.user.id if request.user.is_authenticated else None
            }
            
            blob_url = save_extracted_text_to_blob(
                original_blob_name=uploaded_file.name,
                extracted_text=extracted_text,
                metadata=metadata
            )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            logger.info(f"Successfully extracted text from {uploaded_file.name}")
            
            # Return response to user with storage confirmation
            response_data = {
                'success': True,
                'text': extracted_text,
                'filename': uploaded_file.name,
                'file_type': file_extension,
                'text_length': len(extracted_text),
                'stored_for_indexing': blob_url is not None
            }
            
            if blob_url:
                response_data['storage_url'] = blob_url
                logger.info(f"Extracted text stored for indexing: {blob_url}")
            else:
                logger.warning(f"Failed to store extracted text for indexing: {uploaded_file.name}")
            
            return JsonResponse(response_data)
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            logger.error(f"Error extracting text from {uploaded_file.name}: {str(e)}")
            
            return JsonResponse({
                'success': False,
                'error': f'Failed to extract text: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error in extract_text_from_file: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
def check_service_status(request):
    """
    Check if Azure Computer Vision service is available.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        JsonResponse: JSON response with service status
    """
    try:
        vision_service = AzureVisionService()
        is_available = vision_service.is_service_available()
        
        return JsonResponse({
            'success': True,
            'service_available': is_available,
            'message': 'Service is available' if is_available else 'Service is not available'
        })
        
    except Exception as e:
        logger.error(f"Error checking service status: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'service_available': False,
            'error': str(e)
        }, status=500)


@login_required
def get_supported_formats(request):
    """
    Get list of supported file formats for text extraction.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        JsonResponse: JSON response with supported formats
    """
    supported_formats = {
        'images': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif'],
        'documents': ['.pdf'],
        'max_file_size_mb': 10
    }
    
    return JsonResponse({
        'success': True,
        'supported_formats': supported_formats
    }) 