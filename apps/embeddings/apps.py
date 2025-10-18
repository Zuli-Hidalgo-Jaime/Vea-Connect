from django.apps import AppConfig
from typing import Literal


class EmbeddingsConfig(AppConfig):
    default_auto_field: Literal['django.db.models.BigAutoField'] = 'django.db.models.BigAutoField'
    name = 'apps.embeddings'
    verbose_name = 'Embeddings' 