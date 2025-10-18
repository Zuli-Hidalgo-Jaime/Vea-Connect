# Azure Computer Vision Integration

This document describes the integration of Azure Computer Vision services into the VEA Connect application for text extraction from images and PDF documents.

## Overview

The Azure Computer Vision integration provides the following capabilities:

- **OCR (Optical Character Recognition)**: Extract text from images using Azure Computer Vision
- **Document Analysis**: Extract text from PDF documents using Azure Form Recognizer
- **Text Cleaning**: Remove emojis and special characters from extracted text

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Azure Computer Vision Configuration
VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com/
VISION_KEY=your-vision-api-key
```

### Azure Resource Setup

1. Create an Azure Computer Vision resource in the Azure portal
2. Get the endpoint URL and API key from the resource
3. Ensure the resource supports both Computer Vision and Form Recognizer services

## Usage

### Basic Usage

```python
from apps.vision.azure_vision_service import AzureVisionService

# Initialize the service
vision_service = AzureVisionService()

# Extract text from an image
text_from_image = vision_service.extract_text_from_image("path/to/image.jpg")

# Extract text from a PDF
text_from_pdf = vision_service.extract_text_from_pdf("path/to/document.pdf")

# Check service availability
is_available = vision_service.is_service_available()
```

### Supported File Formats

#### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif)
- TIFF (.tiff, .tif)

#### Documents
- PDF (.pdf)

### Error Handling

The service includes comprehensive error handling:

```python
try:
    text = vision_service.extract_text_from_image("image.jpg")
except FileNotFoundError:
    print("Image file not found")
except ValueError as e:
    print(f"Invalid file format: {e}")
except Exception as e:
    print(f"Extraction failed: {e}")
```

## Testing

### Unit Tests

Run the unit tests to verify the service functionality:

```bash
python manage.py test tests.unit.test_azure_vision_service
```

### Manual Testing

Use the provided test script for manual testing:

```bash
# Test service availability
python scripts/test_azure_vision.py --test-service

# Test image text extraction
python scripts/test_azure_vision.py --image path/to/image.jpg

# Test PDF text extraction
python scripts/test_azure_vision.py --pdf path/to/document.pdf

# Create a test image
python scripts/test_azure_vision.py --create-test-image
```

## Service Architecture

### AzureVisionService Class

The main service class provides the following methods:

- `__init__()`: Initialize the service with Azure credentials
- `extract_text_from_image(file_path)`: Extract text from images
- `extract_text_from_pdf(file_path)`: Extract text from PDFs
- `_clean_text(text)`: Clean extracted text
- `is_service_available()`: Check service availability

### Dependencies

- `azure-cognitiveservices-vision-computervision`: For image OCR
- `azure-ai-formrecognizer`: For PDF document analysis
- `Pillow`: For test image creation (optional)

## Integration with Django

The service is integrated into the Django application as a separate app (`apps.vision`) and can be used in:

- Django views
- Django management commands
- Background tasks
- API endpoints

### Example Django View

```python
from django.http import JsonResponse
from apps.vision.azure_vision_service import AzureVisionService

def extract_text_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        
        # Save uploaded file temporarily
        with open(f'/tmp/{uploaded_file.name}', 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        try:
            vision_service = AzureVisionService()
            
            if uploaded_file.name.lower().endswith('.pdf'):
                text = vision_service.extract_text_from_pdf(f'/tmp/{uploaded_file.name}')
            else:
                text = vision_service.extract_text_from_image(f'/tmp/{uploaded_file.name}')
            
            return JsonResponse({'text': text, 'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False})
    
    return JsonResponse({'error': 'No file provided', 'success': False})
```

## Security Considerations

1. **API Key Security**: Never commit API keys to version control
2. **File Validation**: Always validate uploaded files before processing
3. **Error Handling**: Implement proper error handling to avoid exposing sensitive information
4. **Rate Limiting**: Consider implementing rate limiting for the service

## Performance Considerations

1. **File Size**: Large files may take longer to process
2. **Concurrent Requests**: Azure services have rate limits
3. **Caching**: Consider caching results for frequently processed files
4. **Async Processing**: For large files, consider using background tasks

## Troubleshooting

### Common Issues

1. **Configuration Errors**
   - Ensure `VISION_ENDPOINT` and `VISION_KEY` are properly set
   - Verify the Azure resource is active and accessible

2. **File Format Issues**
   - Check that the file format is supported
   - Ensure the file is not corrupted

3. **Network Issues**
   - Check internet connectivity
   - Verify Azure service availability

4. **Authentication Errors**
   - Verify API key is correct
   - Check if the key has expired

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('apps.vision').setLevel(logging.DEBUG)
```

## Future Enhancements

Potential improvements for the service:

1. **Batch Processing**: Process multiple files simultaneously
2. **Language Detection**: Detect and handle multiple languages
3. **Layout Analysis**: Extract structured data from documents
4. **Image Preprocessing**: Improve OCR accuracy with image enhancement
5. **Caching Layer**: Implement result caching for better performance 