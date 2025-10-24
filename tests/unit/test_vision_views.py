"""
Tests unitarios para vistas de Vision (ajustados solo a rutas y vistas existentes)
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock, patch

class TestVisionViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_login(self.user)

    @patch('apps.vision.views.AzureVisionService')
    @patch('apps.vision.views.save_extracted_text_to_blob')
    def test_extract_text_from_file_success(self, mock_save, mock_vision_service_class):
        mock_service_instance = Mock()
        mock_service_instance.extract_text_from_pdf.return_value = "Texto extraído de prueba"
        mock_vision_service_class.return_value = mock_service_instance
        mock_save.return_value = "https://test.blob.core.windows.net/test.json"
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n",
            content_type="application/pdf"
        )
        response = self.client.post(reverse('vision:extract_text'), {'file': test_file})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('text', data)
        self.assertEqual(data['text'], "Texto extraído de prueba")

    @patch('apps.vision.views.AzureVisionService')
    def test_extract_text_from_file_no_file(self, mock_vision_service_class):
        response = self.client.post(reverse('vision:extract_text'), {})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    @patch('apps.vision.views.AzureVisionService')
    def test_extract_text_from_file_invalid_format(self, mock_vision_service_class):
        test_file = SimpleUploadedFile(
            "test_document.txt",
            b"Este es un archivo de texto plano",
            content_type="text/plain"
        )
        response = self.client.post(reverse('vision:extract_text'), {'file': test_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    @patch('apps.vision.views.AzureVisionService')
    def test_extract_text_from_file_service_error(self, mock_vision_service_class):
        mock_service_instance = Mock()
        mock_service_instance.extract_text_from_pdf.side_effect = Exception("Error de servicio")
        mock_vision_service_class.return_value = mock_service_instance
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n",
            content_type="application/pdf"
        )
        response = self.client.post(reverse('vision:extract_text'), {'file': test_file})
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_vision_service_status_view(self):
        response = self.client.get(reverse('vision:service_status'))
        # Puede ser 200 o 500 dependiendo de la config, pero siempre debe devolver JSON
        self.assertIn(response.status_code, [200, 500])
        data = response.json()
        self.assertIn('success', data)

    def test_vision_supported_formats_view(self):
        response = self.client.get(reverse('vision:supported_formats'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('supported_formats', data) 