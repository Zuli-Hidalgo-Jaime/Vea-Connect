# apps/directory/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Contact
from .forms import ContactForm
from django.db import models
import logging

logger = logging.getLogger(__name__)

def contact_create(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contacto guardado correctamente.")
            return redirect('directory:contact_list')
    else:
        form = ContactForm()
    return render(request, 'directory/create.html', {'form': form})


def contact_list(request):
    q = request.GET.get('q', '').strip()
    ministry = request.GET.get('ministry', '').strip()
    contacts = Contact.objects.all()
    if q:
        contacts = contacts.filter(
            models.Q(first_name__icontains=q) |
            models.Q(last_name__icontains=q) |
            models.Q(role__icontains=q) |
            models.Q(ministry__icontains=q) |
            models.Q(contact__icontains=q)
        )
    if ministry:
        contacts = contacts.filter(ministry__icontains=ministry)
    ministries = Contact.objects.values_list('ministry', flat=True).distinct()
    return render(request, 'directory/directory.html', {
        'contacts': contacts,
        'q': q,
        'ministries': ministries,
        'selected_ministry': ministry,
    })


def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Contacto actualizado correctamente.")
            return redirect('directory:contact_list')
    else:
        form = ContactForm(instance=contact)
    return render(request, 'directory/edit.html', {'form': form, 'contact': contact})


def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    
    if request.method == 'POST':
        try:
            contact_name = f"{contact.first_name} {contact.last_name}"
            contact.delete()
            messages.success(request, f"Contacto '{contact_name}' eliminado correctamente.")
            logger.info(f"Contacto eliminado: {contact_name} (ID: {pk})")
            return redirect('directory:contact_list')
        except Exception as e:
            logger.error(f"Error eliminando contacto {pk}: {str(e)}")
            messages.error(request, f"Error al eliminar el contacto: {str(e)}")
            return redirect('directory:contact_list')
    
    # Para solicitudes GET, mostrar la página de confirmación
    return render(request, 'directory/delete.html', {'contact': contact})
