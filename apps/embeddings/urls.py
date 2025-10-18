from django.urls import path
from . import views

app_name = 'embeddings'

urlpatterns = [
    path('home/', views.list_embeddings, name='home'),
    path('create/', views.create_embedding, name='create'),
    path('list/', views.list_embeddings, name='list'),
    path('delete/<uuid:pk>/', views.delete_embedding, name='delete'),
    path('bulk_upload/', views.bulk_upload, name='bulk_upload'),
] 