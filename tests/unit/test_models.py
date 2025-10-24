
"""
Unit tests for application models
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.core.models import CustomUser
    from apps.directory.models import Contact
    from apps.documents.models import Document
    from apps.events.models import Event
    from apps.donations.models import Donation, DonationType


class CustomUserModelTest(TestCase):
    """Tests for CustomUser model"""

    def test_create_user(self):
        """Test normal user creation"""
        from apps.core.models import CustomUser
        user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test superuser creation"""
        from apps.core.models import CustomUser
        admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        self.assertEqual(admin.email, 'admin@example.com')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_string_representation(self):
        """Test user string representation"""
        from apps.core.models import CustomUser
        user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
        self.assertEqual(str(user), 'test@example.com')

    def test_user_email_unique(self):
        """Test that email is unique"""
        from apps.core.models import CustomUser
        CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser1'
        )
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                email='test@example.com',
                username='testuser2'
            )


class ContactModelTest(TestCase):
    """Tests for Contact model"""

    def test_create_contact(self):
        """Test contact creation"""
        from apps.directory.models import Contact
        contact = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            role="Pastor",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        self.assertEqual(contact.first_name, "Juan")
        self.assertEqual(contact.last_name, "Pérez")
        self.assertEqual(contact.role, "Pastor")
        self.assertEqual(contact.ministry, "Ministerio de Jóvenes")
        self.assertEqual(contact.contact, "juan@iglesia.com")
        self.assertIsNotNone(contact.created_at)

    def test_contact_string_representation(self):
        """Test contact string representation"""
        from apps.directory.models import Contact
        contact = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        self.assertEqual(str(contact), "Juan Pérez")

    def test_contact_ordering(self):
        """Test contact ordering by last name and first name"""
        from apps.directory.models import Contact
        contact2 = Contact.objects.create(
            first_name="Ana",
            last_name="García",
            ministry="Ministerio de Mujeres",
            contact="ana@iglesia.com"
        )
        contact1 = Contact.objects.create(
            first_name="Juan",
            last_name="Pérez",
            ministry="Ministerio de Jóvenes",
            contact="juan@iglesia.com"
        )
        contacts = Contact.objects.all()
        self.assertEqual(contacts[0], contact2)  # Ana García (García < Pérez alphabetically)
        self.assertEqual(contacts[1], contact1)  # Juan Pérez


class DocumentModelTest(TestCase):
    """Tests for Document model"""

    def setUp(self):
        from apps.core.models import CustomUser
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser'
        )

    def test_create_document(self):
        """Test document creation"""
        from apps.documents.models import Document
        document = Document.objects.create(
            title="Test Document",
            description="Test description",
            category="eventos_generales",
            user=self.user
        )
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.description, "Test description")
        self.assertEqual(document.category, "eventos_generales")
        self.assertEqual(document.user, self.user)
        self.assertFalse(document.is_processed)
        self.assertEqual(document.processing_status, "pendiente")

    def test_document_string_representation(self):
        """Test document string representation"""
        from apps.documents.models import Document
        document = Document.objects.create(
            title="Test Document",
            category="eventos_generales",
            user=self.user
        )
        self.assertEqual(str(document), "Test Document")

    def test_document_ordering(self):
        """Test document ordering by date"""
        from apps.documents.models import Document
        # Create documents with different dates
        old_date = timezone.now() - timedelta(days=1)
        recent_date = timezone.now()
        
        document1 = Document.objects.create(
            title="Old Document",
            category="eventos_generales",
            user=self.user,
            date=old_date
        )
        document2 = Document.objects.create(
            title="Recent Document",
            category="ministerios",
            user=self.user,
            date=recent_date
        )
        documents = Document.objects.all()
        self.assertEqual(documents[0], document2)  # Most recent first
        self.assertEqual(documents[1], document1)  # Oldest after

    def test_document_category_choices(self):
        """Test valid category options"""
        from apps.documents.models import Document
        valid_categories = [
            "eventos_generales",
            "ministerios", 
            "formacion",
            "campanas",
            "avisos_globales"
        ]
        for category in valid_categories:
            document = Document.objects.create(
                title=f"Document {category}",
                category=category,
                user=self.user
            )
            self.assertEqual(document.category, category)


class EventModelTest(TestCase):
    """Tests for Event model"""

    def test_create_event(self):
        """Test event creation"""
        from apps.events.models import Event
        event = Event.objects.create(
            title="Test Event",
            description="Event description",
            date="2024-12-25",
            time="18:00:00",
            location="Main Church"
        )
        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.description, "Event description")
        self.assertEqual(str(event.date), "2024-12-25")
        self.assertEqual(str(event.time), "18:00:00")
        self.assertEqual(event.location, "Main Church")
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_string_representation(self):
        """Test event string representation"""
        from apps.events.models import Event
        event = Event.objects.create(
            title="Test Event",
            date="2024-12-25"
        )
        self.assertEqual(str(event), "Test Event - 2024-12-25")

    def test_event_ordering(self):
        """Test event ordering by date and time"""
        from apps.events.models import Event
        event1 = Event.objects.create(
            title="Old Event",
            date="2024-12-24",
            time="18:00:00"
        )
        event2 = Event.objects.create(
            title="Recent Event",
            date="2024-12-25",
            time="19:00:00"
        )
        events = Event.objects.all()
        self.assertEqual(events[0], event2)  # Most recent first
        self.assertEqual(events[1], event1)  # Oldest after


class DonationTypeModelTest(TestCase):
    """Tests for DonationType model"""

    def test_create_donation_type(self):
        """Test donation type creation"""
        from apps.donations.models import DonationType
        donation_type = DonationType.objects.create(name="Monetary")
        self.assertEqual(donation_type.name, "Monetary")

    def test_donation_type_string_representation(self):
        """Test donation type string representation"""
        from apps.donations.models import DonationType
        donation_type = DonationType.objects.create(name="In Kind")
        self.assertEqual(str(donation_type), "In Kind")

    def test_donation_type_unique_name(self):
        """Test that donation type name is unique"""
        from apps.donations.models import DonationType
        DonationType.objects.create(name="Monetary")
        with self.assertRaises(Exception):
            DonationType.objects.create(name="Monetary")


class DonationModelTest(TestCase):
    """Tests for Donation model"""

    def setUp(self):
        from apps.core.models import CustomUser
        from apps.donations.models import DonationType
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
        self.donation_type = DonationType.objects.create(name="Monetary")

    def test_create_donation(self):
        """Test donation creation"""
        from apps.donations.models import Donation
        donation = Donation.objects.create(
            title="Test Donation",
            donation_type=self.donation_type,
            amount=Decimal('100.00'),
            description="Donation description",
            method="deposito",
            entity="Bank of Mexico",
            bank="Banamex",
            clabe="012345678901234567",
            location="Central Branch",
            created_by=self.user
        )
        self.assertEqual(donation.title, "Test Donation")
        self.assertEqual(donation.donation_type, self.donation_type)
        self.assertEqual(donation.amount, Decimal('100.00'))
        self.assertEqual(donation.description, "Donation description")
        self.assertEqual(donation.method, "deposito")
        self.assertEqual(donation.entity, "Bank of Mexico")
        self.assertEqual(donation.bank, "Banamex")
        self.assertEqual(donation.clabe, "012345678901234567")
        self.assertEqual(donation.location, "Central Branch")
        self.assertEqual(donation.created_by, self.user)
        self.assertIsNotNone(donation.created_at)

    def test_donation_negative_amount_validation(self):
        """Test that donation cannot be created with negative amount"""
        from apps.donations.models import Donation
        from django.core.exceptions import ValidationError
        
        donation = Donation(
            title="Negative Donation",
            donation_type=self.donation_type,
            amount=Decimal('-100.00'),
            created_by=self.user
        )
        
        # Test that full_clean raises ValidationError
        with self.assertRaises(ValidationError):
            donation.full_clean()
        
        # Test that save() also raises ValidationError
        with self.assertRaises(ValidationError):
            donation.save()

    def test_donation_string_representation(self):
        """Test donation string representation"""
        from apps.donations.models import Donation
        donation = Donation.objects.create(
            title="Test Donation",
            donation_type=self.donation_type,
            created_by=self.user
        )
        expected_str = f"Test Donation - {donation.created_at.strftime('%d/%m/%Y')}"
        self.assertEqual(str(donation), expected_str)

    def test_donation_ordering(self):
        """Test donation ordering by creation date"""
        from apps.donations.models import Donation
        from django.utils import timezone
        import time
        
        # Create old donation with specific date
        old_time = timezone.now() - timezone.timedelta(hours=1)
        donation1 = Donation.objects.create(
            title="Old Donation",
            donation_type=self.donation_type,
            created_by=self.user,
            created_at=old_time
        )
        
        # Create recent donation with specific date
        new_time = timezone.now()
        donation2 = Donation.objects.create(
            title="Recent Donation",
            donation_type=self.donation_type,
            created_by=self.user,
            created_at=new_time
        )
        
        donations = Donation.objects.order_by('-created_at')
        self.assertEqual(donations[0], donation2)  # Most recent first
        self.assertEqual(donations[1], donation1)  # Oldest after

    def test_donation_method_choices(self):
        """Test valid method options"""
        from apps.donations.models import Donation
        valid_methods = [
            'deposito',
            'transferencia',
            'relaciones_publicas',
            'ministerio',
            'entrega_directa'
        ]
        
        for method in valid_methods:
            donation = Donation.objects.create(
                title=f"Donation {method}",
                donation_type=self.donation_type,
                method=method,
                created_by=self.user
            )
            self.assertEqual(donation.method, method)

    def test_donation_type_choices(self):
        """Test valid type options"""
        from apps.donations.models import DonationType, Donation
        valid_types = [
            'monetaria',
            'especie',
            'medicamentos',
            'voluntariado',
            'otros'
        ]
        for donation_type_name in valid_types:
            donation_type, _ = DonationType.objects.get_or_create(name=donation_type_name)
            donation = Donation.objects.create(
                title=f"Donation {donation_type_name}",
                donation_type=donation_type,
                created_by=self.user
            )
            self.assertEqual(donation.donation_type, donation_type) 