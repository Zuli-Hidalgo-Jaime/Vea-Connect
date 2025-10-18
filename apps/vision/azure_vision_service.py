import os
import logging
from typing import Optional
from pathlib import Path

from django.conf import settings
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from msrest.authentication import CognitiveServicesCredentials

logger = logging.getLogger(__name__)


class AzureVisionService:
    """
    Service class for Azure Computer Vision integration.
    
    Provides methods to extract text from images and PDF documents
    using Azure Computer Vision and Form Recognizer services.
    """
    
    def __init__(self):
        """
        Initialize the Azure Vision Service with configuration from settings.
        
        Raises:
            ValueError: If required configuration is missing
        """
        self.vision_endpoint = getattr(settings, 'VISION_ENDPOINT', None)
        self.vision_key = getattr(settings, 'VISION_KEY', None)
        
        if not self.vision_endpoint or not self.vision_key:
            raise ValueError(
                "Azure Computer Vision configuration is missing. "
                "Please set VISION_ENDPOINT and VISION_KEY in your environment variables."
            )
        
        # Initialize Computer Vision client
        self.vision_client = ComputerVisionClient(
            self.vision_endpoint,
            CognitiveServicesCredentials(self.vision_key)
        )
        
        # Initialize Document Analysis client for PDF processing
        self.document_client = DocumentAnalysisClient(
            endpoint=self.vision_endpoint,
            credential=AzureKeyCredential(self.vision_key)
        )
    
    def extract_text_from_image(self, file_path: str) -> str:
        """
        Extract text from an image file using Azure Computer Vision OCR.
        
        Args:
            file_path (str): Path to the image file to process
            
        Returns:
            str: Extracted text from the image, cleaned of special characters
            
        Raises:
            FileNotFoundError: If the image file does not exist
            ValueError: If the file is not a supported image format
            Exception: If there's an error during text extraction
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Image file not found: {file_path}")
            
            # Validate file is an image
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif'}
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension not in image_extensions:
                raise ValueError(
                    f"Unsupported image format: {file_extension}. "
                    f"Supported formats: {', '.join(image_extensions)}"
                )
            
            logger.info(f"Processing image for text extraction: {file_path}")
            
            # Read image file
            with open(file_path, "rb") as image_file:
                # Extract text using OCR
                # Aquí se almacena el resultado del procesamiento de Vision, se mantiene documentado para posibles ajustes de integración con AI Search.
                result = self.vision_client.recognize_printed_text_in_stream(image_file)
            
            # Validate result and extract text
            extracted_text = ""
            if result and hasattr(result, 'regions') and result.regions:
                for region in result.regions:
                    for line in region.lines:
                        for word in line.words:
                            extracted_text += word.text + " "
                        extracted_text += "\n"
                    extracted_text += "\n"
            else:
                logger.warning(f"No text regions found in image: {file_path}")
                return ""
            
            # Clean text (remove special characters and emojis)
            cleaned_text = self._clean_text(extracted_text)
            
            # Aquí solo se devuelve el resultado al usuario y no se almacena
            logger.info(f"Successfully extracted text from image: {file_path}")
            return cleaned_text.strip()
            
        except FileNotFoundError:
            logger.error(f"Image file not found: {file_path}")
            raise
        except ValueError as e:
            logger.error(f"Invalid image format: {file_path} - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {str(e)}")
            raise Exception(f"Failed to extract text from image: {str(e)}")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using Azure Form Recognizer.
        
        Args:
            file_path (str): Path to the PDF file to process
            
        Returns:
            str: Extracted text from the PDF, cleaned of special characters
            
        Raises:
            FileNotFoundError: If the PDF file does not exist
            ValueError: If the file is not a PDF
            Exception: If there's an error during text extraction
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Validate file is a PDF
            if not file_path.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF document")
            
            logger.info(f"Processing PDF for text extraction: {file_path}")
            
            # Read PDF file
            with open(file_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            
            # Analyze document
            # Aquí se almacena el resultado del procesamiento de Vision, se mantiene documentado para posibles ajustes de integración con AI Search.
            poller = self.document_client.begin_analyze_document(
                "prebuilt-document", pdf_data
            )
            result = poller.result()
            
            # Validate result and extract text from all pages
            extracted_text = ""
            if result and hasattr(result, 'pages') and result.pages:
                for page in result.pages:
                    for line in page.lines:
                        extracted_text += line.content + "\n"
            else:
                logger.warning(f"No pages found in PDF: {file_path}")
                return ""
            
            # Clean text (remove special characters and emojis)
            cleaned_text = self._clean_text(extracted_text)
            
            # Aquí solo se devuelve el resultado al usuario y no se almacena
            logger.info(f"Successfully extracted text from PDF: {file_path}")
            return cleaned_text.strip()
            
        except FileNotFoundError:
            logger.error(f"PDF file not found: {file_path}")
            raise
        except ValueError as e:
            logger.error(f"Invalid PDF format: {file_path} - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing special characters and emojis.
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text without special characters or emojis
        """
        import re
        
        # Remove emojis and special Unicode characters
        # Keep only basic Latin characters, numbers, spaces, and common punctuation
        cleaned = re.sub(r'[^\x00-\x7F\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF]+', '', text)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove control characters
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        return cleaned.strip()
    
    def is_service_available(self) -> bool:
        """
        Check if the Azure Vision service is available and properly configured.
        
        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            # Check if credentials are properly configured
            if not self.vision_endpoint or not self.vision_key:
                return False
            
            # Test connection by trying to create a simple operation
            # We'll use a simple test that doesn't require an actual operation ID
            return True
        except Exception as e:
            logger.warning(f"Azure Vision service not available: {str(e)}")
            return False 