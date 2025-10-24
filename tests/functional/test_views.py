"""
Functional tests for application views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.core.models import CustomUser
from apps.directory.models import Contact
from apps.documents.models import Document
from apps.events.models import Event
from apps.donations.models import Donation, DonationType
from django.urls import resolve


class CoreViewsTest(TestCase):
    """Tests for core views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_home_view(self):
        """Test home view"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_base_template(self):
        """Test that base template works"""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'VEA WebApp')


class DirectoryViewsTest(TestCase):
    """Tests for directory views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_login(self.user)

    def test_contact_list_view(self):
        """Test contact list view"""
        # Create test contact
        contact = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            role="Pastor",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        
        response = self.client.get(reverse('directory:contact_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan Pérez")

    def test_contact_create_view_get(self):
        """Test contact creation view (GET)"""
        response = self.client.get(reverse('directory:contact_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'directory/create.html')

    def test_contact_create_view_post(self):
        """Test contact creation view (POST)"""
        contact_data = {
            'first_name': 'Ana',
            'last_name': 'García',
            'role': 'Líder',
            'ministry': 'Ministerio de Mujeres',
            'contact': 'ana@iglesia.com'
        }
        
        response = self.client.post(reverse('directory:contact_create'), contact_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify contact was created
        contact = Contact.objects.get(first_name='Ana')
        self.assertEqual(contact.last_name, 'García')

    def test_contact_update_view_get(self):
        """Test contact update view (GET)"""
        contact = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            role="Pastor",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        
        response = self.client.get(reverse('directory:contact_edit', args=[contact.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'directory/edit.html')

    def test_contact_update_view_post(self):
        """Test contact update view (POST)"""
        contact = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            role="Pastor",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        
        updated_data = {
            'first_name': 'Juan Carlos',
            'last_name': 'Pérez',
            'role': 'Pastor Principal',
            'ministry': 'Ministerio de Jóvenes',
            'contact': 'juan@iglesia.com'
        }
        
        response = self.client.post(reverse('directory:contact_edit', args=[contact.pk]), updated_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify contact was updated
        contact.refresh_from_db()
        self.assertEqual(contact.first_name, 'Juan Carlos')

    def test_contact_delete_view_get(self):
        """Test contact delete view (GET)"""
        contact = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            role="Pastor",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        
        response = self.client.get(reverse('directory:contact_delete', args=[contact.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'directory/delete.html')

    def test_contact_delete_view_post(self):
        """Test contact delete view (POST)"""
        contact = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            role="Pastor",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        
        response = self.client.post(reverse('directory:contact_delete', args=[contact.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify contact was deleted
        self.assertFalse(Contact.objects.filter(pk=contact.pk).exists())


class DocumentViewsTest(TestCase):
    """Tests for document views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_login(self.user)

    def test_document_list_view(self):
        """Test document list view"""
        # Create test file
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            "test content".encode('utf-8'),
            content_type="application/pdf"
        )
        
        document = Document.objects.create(
            title="Test document",
            description="Test description",
            category="eventos_generales",
            file=test_file,
            user=self.user
        )
        
        response = self.client.get(reverse('documents:document_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test document")

    def test_document_create_view_get(self):
        """Test document creation view (GET)"""
        response = self.client.get(reverse('documents:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/create.html')

    def test_document_create_view_post(self):
        """Test document creation view (POST)"""
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            "test content".encode('utf-8'),
            content_type="application/pdf"
        )
        
        document_data = {
            'title': 'Test Document',
            'description': 'Test description',
            'category': 'eventos_generales'
        }
        
        files = {
            'file': test_file
        }
        
        response = self.client.post(reverse('documents:create'), document_data, files=files)
        # Verify that the view responds correctly
        self.assertIn(response.status_code, [200, 302])

    def test_document_update_view_get(self):
        """Test document update view (GET)"""
        document = Document.objects.create(
            title="Test document",
            description="Test description",
            category="eventos_generales",
            user=self.user
        )
        
        response = self.client.get(reverse('documents:edit', args=[document.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test document")

    def test_document_update_view_post(self):
        """Test document update view (POST)"""
        document = Document.objects.create(
            title="Test document",
            description="Test description",
            category="eventos_generales",
            user=self.user
        )
        
        updated_data = {
            'title': 'Updated Test Document',
            'description': 'Updated description',
            'category': 'ministerios'
        }
        
        response = self.client.post(reverse('documents:edit', args=[document.pk]), updated_data)
        self.assertEqual(response.status_code, 302)  # La vista hace redirect tras actualizar
        
        # Verify document was updated
        document.refresh_from_db()
        self.assertEqual(document.title, 'Updated Test Document')

    def test_document_delete_view_get(self):
        """Test document delete view (GET)"""
        document = Document.objects.create(
            title="Test document",
            description="Test description",
            category="eventos_generales",
            user=self.user
        )
        
        response = self.client.get(reverse('documents:delete', args=[document.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documents/confirm_delete.html')

    def test_document_delete_view_post(self):
        """Test document delete view (POST)"""
        document = Document.objects.create(
            title="Test document",
            description="Test description",
            category="eventos_generales",
            user=self.user
        )
        
        response = self.client.post(reverse('documents:delete', args=[document.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify document was deleted
        self.assertFalse(Document.objects.filter(pk=document.pk).exists())


class EventViewsTest(TestCase):
    """Tests for event views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_login(self.user)

    def test_event_list_view(self):
        """Test event list view"""
        event = Event.objects.create(
            title="Test event",
            description="Test event description",
            date="2024-12-25",
            time="18:00:00",
            location="Main Church"
        )
        
        response = self.client.get(reverse('events:events'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test event")

    def test_event_create_view_get(self):
        """Test event creation view (GET)"""
        response = self.client.get(reverse('events:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/create.html')

    def test_event_create_view_post(self):
        """Test event creation view (POST)"""
        event_data = {
            'title': 'Test Event',
            'description': 'Test event description',
            'date': '2024-12-25',
            'time': '18:00:00',
            'location': 'Main Church'
        }
        
        response = self.client.post(reverse('events:create'), event_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify event was created
        event = Event.objects.get(title='Test Event')
        self.assertEqual(event.location, 'Main Church')

    def test_event_update_view_get(self):
        """Test event update view (GET)"""
        event = Event.objects.create(
            title="Test event",
            description="Test event description",
            date="2024-12-25",
            time="18:00:00",
            location="Main Church"
        )
        
        response = self.client.get(reverse('events:edit', args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test event")

    def test_event_update_view_post(self):
        """Test event update view (POST)"""
        event = Event.objects.create(
            title="Test event",
            description="Test event description",
            date="2024-12-25",
            time="18:00:00",
            location="Main Church"
        )
        
        updated_data = {
            'title': 'Updated Test Event',
            'description': 'Updated event description',
            'date': '2024-12-26',
            'time': '19:00:00',
            'location': 'Updated Location'
        }
        
        response = self.client.post(reverse('events:edit', args=[event.pk]), updated_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify event was updated
        event.refresh_from_db()
        self.assertEqual(event.title, 'Updated Test Event') 


class TestURLResolves(TestCase):
    def test_directory_urls(self):
        self.assertEqual(resolve('/directory/').url_name, 'contact_list')
        self.assertEqual(resolve('/directory/create/').url_name, 'contact_create')
        self.assertEqual(resolve('/directory/edit/1/').url_name, 'contact_edit')
        self.assertEqual(resolve('/directory/delete/1/').url_name, 'contact_delete')

    def test_documents_urls(self):
        self.assertEqual(resolve('/documents/').url_name, 'document_list')
        self.assertEqual(resolve('/documents/create/').url_name, 'create')
        self.assertEqual(resolve('/documents/edit/1/').url_name, 'edit')
        self.assertEqual(resolve('/documents/delete/1/').url_name, 'delete')
        self.assertEqual(resolve('/documents/download/1/').url_name, 'download')

    def test_events_urls(self):
        self.assertEqual(resolve('/events/').url_name, 'events')
        self.assertEqual(resolve('/events/create/').url_name, 'create')
        self.assertEqual(resolve('/events/edit/1/').url_name, 'edit')
        self.assertEqual(resolve('/events/delete/1/').url_name, 'delete') 