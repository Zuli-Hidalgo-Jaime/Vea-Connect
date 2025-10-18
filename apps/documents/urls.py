from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='document_list'),       # Lista de documentos
    path('create/', views.upload_document, name='create'), # Subir documento
    path('edit/<int:pk>/', views.edit_document, name='edit'), # Editar documento
    path('delete/<int:pk>/', views.delete_document, name='delete'), # Eliminar documento
    path('download/<int:pk>/', views.download_document, name='download'), # Descargar documento
]
