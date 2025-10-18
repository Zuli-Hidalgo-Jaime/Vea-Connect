# apps/events/urls.py

from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='events'),     # Muestra el template 'events.html'
    path('create/', views.event_create, name='create'),  # Formulario de creación
    path('edit/<int:pk>/', views.event_edit, name='edit'),
    path('delete/<int:pk>/', views.event_delete, name='delete'),
]
