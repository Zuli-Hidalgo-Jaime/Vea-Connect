# apps/user_settings/urls.py

from django.urls import path
from . import views

app_name = 'user_settings'

urlpatterns = [
    # Vista de perfil/configuración de usuario (requiere template user_settings/profile.html)
    path('', views.profile, name='profile'),
]
