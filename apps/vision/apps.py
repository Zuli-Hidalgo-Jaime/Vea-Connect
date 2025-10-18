from django.apps import AppConfig


class VisionConfig(AppConfig):
    """
    Configuration class for the Vision app.
    
    This app provides Azure Computer Vision integration for text extraction
    from images and PDF documents.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vision'
    verbose_name = 'Azure Computer Vision' 