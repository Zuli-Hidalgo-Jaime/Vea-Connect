from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import tempfile
from pathlib import Path

from apps.vision.azure_vision_service import AzureVisionService


class Command(BaseCommand):
    """
    Django management command to test Azure Computer Vision service.
    
    This command provides a simple way to test the AzureVisionService
    functionality from the command line.
    """
    
    help = 'Test Azure Computer Vision service functionality'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--check-service',
            action='store_true',
            help='Check if Azure Vision service is available'
        )
        parser.add_argument(
            '--image',
            type=str,
            help='Path to image file for text extraction test'
        )
        parser.add_argument(
            '--pdf',
            type=str,
            help='Path to PDF file for text extraction test'
        )
        parser.add_argument(
            '--create-test-image',
            action='store_true',
            help='Create a test image with text for testing'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Azure Computer Vision service test')
        )
        self.stdout.write('=' * 60)
        
        # Check if any specific test was requested
        if not any([
            options['check_service'],
            options['image'],
            options['pdf'],
            options['create_test_image']
        ]):
            self.stdout.write(
                self.style.WARNING('No specific test specified. Running service check...')
            )
            options['check_service'] = True
        
        # Check service availability
        if options['check_service']:
            self.check_service_availability()
        
        # Create test image
        if options['create_test_image']:
            self.create_test_image()
        
        # Test image text extraction
        if options['image']:
            self.test_image_extraction(options['image'])
        
        # Test PDF text extraction
        if options['pdf']:
            self.test_pdf_extraction(options['pdf'])
        
        self.stdout.write(
            self.style.SUCCESS('🏁 Test completed')
        )
    
    def check_service_availability(self):
        """Check if Azure Vision service is available."""
        self.stdout.write('Testing Azure Vision service availability...')
        
        try:
            # Check if configuration is available
            if not (getattr(settings, 'VISION_ENDPOINT', None) and 
                    getattr(settings, 'VISION_KEY', None)):
                self.stdout.write(
                    self.style.ERROR('❌ Azure Computer Vision configuration is missing')
                )
                self.stdout.write('Please set VISION_ENDPOINT and VISION_KEY in your environment')
                return
            
            # Initialize service
            service = AzureVisionService()
            is_available = service.is_service_available()
            
            if is_available:
                self.stdout.write(
                    self.style.SUCCESS('✅ Azure Vision service is available and properly configured')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Azure Vision service is not available')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing service availability: {str(e)}')
            )
    
    def create_test_image(self):
        """Create a test image with text."""
        self.stdout.write('Creating test image with text...')
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple image with text
            width, height = 800, 400
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Try to use a default font, fallback to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Add test text
            test_text = "Hello World! This is a test image for Azure Computer Vision OCR."
            text_bbox = draw.textbbox((0, 0), test_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), test_text, fill='black', font=font)
            
            # Save the image
            test_image_path = "test_image_ocr.jpg"
            image.save(test_image_path)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created test image: {test_image_path}')
            )
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING('⚠️ PIL/Pillow not available, cannot create test image')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating test image: {str(e)}')
            )
    
    def test_image_extraction(self, image_path):
        """Test text extraction from an image."""
        self.stdout.write(f'Testing text extraction from image: {image_path}')
        
        try:
            # Validate file exists
            if not os.path.exists(image_path):
                self.stdout.write(
                    self.style.ERROR(f'❌ Image file not found: {image_path}')
                )
                return
            
            # Initialize service
            service = AzureVisionService()
            
            # Extract text
            extracted_text = service.extract_text_from_image(image_path)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Text extraction completed successfully')
            )
            self.stdout.write(f'📄 Extracted text ({len(extracted_text)} characters):')
            self.stdout.write('-' * 50)
            self.stdout.write(extracted_text)
            self.stdout.write('-' * 50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error extracting text from image: {str(e)}')
            )
    
    def test_pdf_extraction(self, pdf_path):
        """Test text extraction from a PDF."""
        self.stdout.write(f'Testing text extraction from PDF: {pdf_path}')
        
        try:
            # Validate file exists
            if not os.path.exists(pdf_path):
                self.stdout.write(
                    self.style.ERROR(f'❌ PDF file not found: {pdf_path}')
                )
                return
            
            # Initialize service
            service = AzureVisionService()
            
            # Extract text
            extracted_text = service.extract_text_from_pdf(pdf_path)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Text extraction completed successfully')
            )
            self.stdout.write(f'📄 Extracted text ({len(extracted_text)} characters):')
            self.stdout.write('-' * 50)
            self.stdout.write(extracted_text)
            self.stdout.write('-' * 50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error extracting text from PDF: {str(e)}')
            ) 