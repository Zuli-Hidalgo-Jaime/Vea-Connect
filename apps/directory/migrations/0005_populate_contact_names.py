# Generated manually to fix data migration issue

from django.db import migrations

def populate_contact_names(apps, schema_editor):
    """Populate first_name and last_name for contacts that don't have them"""
    Contact = apps.get_model('directory', 'Contact')
    
    # Get all contacts that don't have first_name or last_name set
    contacts = Contact.objects.filter(
        first_name__isnull=True, 
        last_name__isnull=True
    )
    
    for contact in contacts:
        # Since we don't have the original name field, we'll set default values
        # This is a fallback for any contacts that might not have been properly migrated
        contact.first_name = "Sin nombre"
        contact.last_name = ""
        contact.save()

def reverse_populate_contact_names(apps, schema_editor):
    """Reverse operation - this is a no-op since we can't restore the original name"""
    # This is intentionally empty since we can't restore the original name field
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0004_alter_contact_first_name_alter_contact_last_name'),
    ]

    operations = [
        migrations.RunPython(populate_contact_names, reverse_populate_contact_names),
    ] 