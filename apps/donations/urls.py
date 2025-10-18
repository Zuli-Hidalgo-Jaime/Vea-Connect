from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('', views.donation_list, name='list'),     # Muestra donations.html
    path('create/', views.donation_create, name='create'), # Muestra create.html
    path('<int:pk>/edit/', views.donation_edit, name='edit'),
    path('<int:pk>/delete/', views.donation_delete, name='delete'),
]
