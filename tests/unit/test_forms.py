"""
Unit tests for forms
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.directory.forms import ContactForm
from apps.documents.forms import DocumentForm
from apps.events.forms import EventForm
from apps.donations.forms import DonationForm
from decimal import Decimal
from typing import cast
from django.forms.utils import ErrorDict


class ContactFormTest(TestCase):
    """Tests for ContactForm"""

    def test_contact_form_valid(self):
        """Test that form is valid with correct data"""
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'role': 'Pastor',
            'ministry': 'Ministerio de Jóvenes',
            'contact': 'juan@iglesia.com'
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_contact_form_invalid(self):
        """Test contact form with invalid data"""
        from apps.directory.forms import ContactForm
        
        form = ContactForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('ministry', errors)
        self.assertIn('contact', errors)

    def test_contact_form_save(self):
        """Test that form saves correctly"""
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'role': 'Pastor',
            'ministry': 'Ministerio de Jóvenes',
            'contact': 'juan@iglesia.com'
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())
        contact = form.save()
        self.assertEqual(contact.first_name, 'Juan')
        self.assertEqual(contact.last_name, 'Pérez')
        self.assertEqual(contact.role, 'Pastor')


class DocumentFormTest(TestCase):
    """Tests for DocumentForm"""

    def test_document_form_valid(self):
        """Test that form is valid with correct data"""
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        form_data = {
            'title': 'Test Document',
            'description': 'Test description',
            'category': 'eventos_generales'
        }
        form_files = {
            'file': test_file
        }
        form = DocumentForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())

    def test_document_form_invalid(self):
        """Test that form is invalid with invalid category"""
        form_data = {
            'title': 'Test Document',
            'description': 'Test description',
            'category': 'invalid_category'
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('category', errors)

    def test_document_category_choices(self):
        """Test valid category options"""
        valid_categories = [
            'eventos_generales',
            'ministerios',
            'formacion',
            'campanas',
            'avisos_globales'
        ]
        
        for category in valid_categories:
            test_file = SimpleUploadedFile(
                f"test_{category}.pdf",
                b"file_content",
                content_type="application/pdf"
            )
            
            form_data = {
                'title': f'Test Document {category}',
                'description': 'Test description',
                'category': category
            }
            form_files = {
                'file': test_file
            }
            form = DocumentForm(data=form_data, files=form_files)
            self.assertTrue(form.is_valid(), f"Form should be valid for category: {category}")

    def test_document_form_save(self):
        """Test that form saves correctly"""
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        form_data = {
            'title': 'Test Document',
            'description': 'Test description',
            'category': 'eventos_generales'
        }
        form_files = {
            'file': test_file
        }
        form = DocumentForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
        document = form.save()
        self.assertEqual(document.title, 'Test Document')
        self.assertEqual(document.description, 'Test description')
        self.assertEqual(document.category, 'eventos_generales')

    def test_document_form_blocked_file_types(self):
        """Test that blocked file types are rejected"""
        blocked_files = [
            ("test.exe", b"executable", "application/x-msdownload"),
            ("script.bat", b"batch", "application/x-bat"),
            ("malware.js", b"javascript", "application/javascript"),
            ("virus.php", b"php", "application/x-httpd-php"),
            ("dangerous.py", b"python", "text/x-python"),
        ]
        
        for filename, content, content_type in blocked_files:
            test_file = SimpleUploadedFile(filename, content, content_type=content_type)
            form_data = {
                'title': 'Test Document',
                'description': 'Test description',
                'category': 'eventos_generales'
            }
            form_files = {'file': test_file}
            form = DocumentForm(data=form_data, files=form_files)
            self.assertFalse(form.is_valid())
            self.assertIsNotNone(form.errors)
            errors = cast(ErrorDict, form.errors)
            self.assertIn('file', errors)
            self.assertIn('No se permite subir archivos ejecutables', str(errors['file']))

    def test_document_form_invalid_file_type(self):
        """Test that invalid file types are rejected"""
        test_file = SimpleUploadedFile(
            "test.xyz",
            b"unknown content",
            content_type="application/unknown"
        )
        form_data = {
            'title': 'Test Document',
            'description': 'Test description',
            'category': 'eventos_generales'
        }
        form_files = {'file': test_file}
        form = DocumentForm(data=form_data, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('file', errors)
        self.assertIn('Tipo de archivo no permitido', str(errors['file']))

    def test_document_form_no_file(self):
        """Test form without file (should be valid)"""
        form_data = {
            'title': 'Test Document',
            'description': 'Test description',
            'category': 'eventos_generales'
        }
        form = DocumentForm(data=form_data)
        self.assertTrue(form.is_valid())


class EventFormTest(TestCase):
    """Tests for EventForm"""

    def test_event_form_valid(self):
        """Test that form is valid with correct data"""
        form_data = {
            'title': 'Test Event',
            'description': 'Event description',
            'date': '2024-12-25',
            'time': '18:00:00',
            'location': 'Main Church'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_event_form_invalid(self):
        """Test that form is invalid without required fields"""
        form_data = {
            'description': 'Event description',
            'date': '2024-12-25'
            # Missing title
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('title', errors)

    def test_event_form_save(self):
        """Test that form saves correctly"""
        form_data = {
            'title': 'Test Event',
            'description': 'Event description',
            'date': '2024-12-25',
            'time': '18:00:00',
            'location': 'Main Church'
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        event = form.save()
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.description, 'Event description')
        self.assertEqual(str(event.date), '2024-12-25')

    def test_event_form_invalid_date_format(self):
        """Test form with invalid date format"""
        form_data = {
            'title': 'Test Event',
            'date': 'invalid-date',
            'time': '18:00:00'
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('date', errors)

    def test_event_form_invalid_time_format(self):
        """Test form with invalid time format"""
        form_data = {
            'title': 'Test Event',
            'date': '2024-12-25',
            'time': 'invalid-time'
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('time', errors)

    def test_event_form_empty_fields(self):
        """Test form with empty optional fields"""
        form_data = {
            'title': 'Test Event',
            'description': '',
            'date': '',
            'time': '',
            'location': ''
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())


class DonationFormTest(TestCase):
    """Tests for DonationForm"""

    def setUp(self):
        from apps.donations.models import DonationType
        self.donation_type = DonationType.objects.create(name="Monetary")
        self.alimento_type = DonationType.objects.create(name="Alimento")
        self.especie_type = DonationType.objects.create(name="Especie")
        from django.contrib.auth import get_user_model
        self.user = get_user_model().objects.create_user(username="testuser", email="test@example.com", password="testpass")

    def test_donation_form_valid(self):
        """Test that form is valid with correct data"""
        form_data = {
            'title': 'Test Donation',
            'donation_type': self.donation_type.id,
            'amount': '100.00',
            'description': 'Donation description',
            'method': 'deposito',
            'entity': 'Bank of Mexico',
            'bank': 'Banamex',
            'clabe': '012345678901234567',
            'location': 'Central Branch'
        }
        form = DonationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_donation_form_invalid(self):
        """Test that form is invalid without required fields"""
        form_data = {
            'description': 'Donation description',
            'method': 'deposito'
            # Missing title and donation_type
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('title', errors)
        self.assertIn('donation_type', errors)

    def test_donation_method_choices(self):
        """Test valid method options"""
        valid_methods = [
            'deposito',
            'transferencia',
            'relaciones_publicas',
            'ministerio',
            'entrega_directa'
        ]
        
        for method in valid_methods:
            form_data = {
                'title': f'Test Donation {method}',
                'donation_type': self.donation_type.id,
                'amount': '100.00',
                'method': method
            }
            form = DonationForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Form should be valid for method: {method}")

    def test_donation_form_save(self):
        """Test donation form save method"""
        from apps.donations.forms import DonationForm
        from apps.donations.models import Donation
        
        form_data = {
            'title': 'Test Donation',
            'donation_type': self.donation_type.pk,
            'amount': '100.00',
            'description': 'Test donation description',
            'method': 'deposito',
            'entity': 'Test Bank',
            'bank': 'Test Bank',
            'clabe': '012345678901234567',
            'location': 'Test Location'
        }
        
        form = DonationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Save with user
        donation = form.save(commit=False)
        donation.created_by = self.user
        donation.save()
        
        self.assertEqual(donation.title, 'Test Donation')
        self.assertEqual(donation.amount, Decimal('100.00'))
        self.assertEqual(donation.created_by, self.user)

    def test_donation_form_alimento_validation(self):
        """Test validation for Alimento donation type"""
        form_data = {
            'title': 'Food Donation',
            'donation_type': self.alimento_type.id,
            'amount': '100.00',  # Should not be allowed
            'bank': 'Test Bank',  # Should not be allowed
            'clabe': '012345678901234567'  # Should not be allowed
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('amount', errors)
        self.assertIn('bank', errors)
        self.assertIn('clabe', errors)

    def test_donation_form_especie_validation(self):
        """Test validation for Especie donation type"""
        form_data = {
            'title': 'In Kind Donation',
            'donation_type': self.especie_type.id,
            'amount': '100.00',  # Should not be allowed
            'bank': 'Test Bank',  # Should not be allowed
            'clabe': '012345678901234567'  # Should not be allowed
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('amount', errors)
        self.assertIn('bank', errors)
        self.assertIn('clabe', errors)

    def test_donation_form_no_donation_type(self):
        """Test form validation without donation type"""
        form_data = {
            'title': 'Test Donation',
            'amount': '100.00'
            # Missing donation_type
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)
        errors = cast(ErrorDict, form.errors)
        self.assertIn('donation_type', errors)

    def test_donation_form_save_with_user(self):
        """Test form save method with user parameter"""
        form_data = {
            'title': 'Test Donation',
            'donation_type': self.donation_type.pk,
            'amount': '100.00'
        }
        form = DonationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        donation = form.save(user=self.user)
        self.assertEqual(donation.created_by, self.user)
        self.assertEqual(donation.donation_type, self.donation_type) 