from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('', views.DonationListView.as_view(), name='list'),
    path('nueva/', views.DonationCreateView.as_view(), name='create'),
    # Agregar aquí rutas para editar, eliminar y ver detalles
]
