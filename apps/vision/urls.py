from django.urls import path
from . import views

app_name = 'vision'
 
urlpatterns = [
    path('extract-text/', views.extract_text_from_file, name='extract_text'),
    path('service-status/', views.check_service_status, name='service_status'),
    path('supported-formats/', views.get_supported_formats, name='supported_formats'),
] 