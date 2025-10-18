from django.apps import AppConfig

class DonationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.donations'

    def ready(self):
        import apps.donations.signals 