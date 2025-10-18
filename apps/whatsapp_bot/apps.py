from django.apps import AppConfig


class WhatsAppBotConfig(AppConfig):
    """
    Configuration for WhatsApp Bot application.
    
    This app provides WhatsApp bot functionality with ACS integration,
    template-based messaging, and intelligent fallback responses.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.whatsapp_bot'
    verbose_name = 'WhatsApp Bot Handler'
    
    def ready(self):
        """Initialize app when Django starts."""
        try:
            # Import signals to register them
            from . import signals
        except ImportError:
            pass 