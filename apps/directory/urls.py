# apps/directory/urls.py

from django.urls import path
from . import views

app_name = 'directory'

urlpatterns = [
    path('', views.contact_list, name='contact_list'),           # Vista principal del directorio
    path('create/', views.contact_create, name='contact_create'), # Vista para crear un nuevo contacto
    path('edit/<int:pk>/', views.contact_edit, name='contact_edit'), # Vista para editar un contacto
    path('delete/<int:pk>/', views.contact_delete, name='contact_delete'), # Vista para eliminar un contacto
]
