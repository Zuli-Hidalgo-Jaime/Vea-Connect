# Generated manually to make contact names required

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0005_populate_contact_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='first_name',
            field=models.CharField(max_length=50, verbose_name='Nombre'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='last_name',
            field=models.CharField(max_length=50, verbose_name='Apellido'),
        ),
    ] 