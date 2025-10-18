from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import Donation
from .forms import DonationForm

@login_required
def donation_list(request):
    """
    Vista principal que muestra las donaciones activas, ordenadas por fecha de creación.
    Incluye búsqueda por título, tipo y entidad.
    """
    query = request.GET.get('q', '').strip()
    donations = Donation.objects.all().order_by('-created_at')
    if query:
        donations = donations.filter(
            Q(title__icontains=query) |
            Q(donation_type__name__icontains=query) |
            Q(entity__icontains=query) |
            Q(description__icontains=query)
        )
    context = {
        'donations': donations,
        'query': query,
    }
    return render(request, 'donations/donations.html', context)

@login_required
def donation_create(request):
    """
    Vista que permite crear una nueva donación.
    Asigna automáticamente el usuario actual como creador.
    """
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            try:
                form.save(user=request.user)
                messages.success(request, 'Donación creada exitosamente.')
                return redirect('donations:list')
            except Exception as e:
                messages.error(request, 'Ocurrió un error al guardar la donación. Por favor, revisa los campos obligatorios e inténtalo de nuevo.')
                logger.error(f"Error creating donation: {str(e)}")
                logger.debug(f"Form data: {form.cleaned_data}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
                    logger.error(f"Error in field {field}: {error}")
    else:
        form = DonationForm()
    
    return render(request, 'donations/donation_form.html', {
        'form': form,
        'action': 'Crear'
    })

@login_required
def donation_edit(request, pk):
    """
    Vista que permite editar una donación existente.
    Solo permite editar al creador o superusuarios.
    """
    donation = get_object_or_404(Donation, pk=pk)
    
    if not request.user.is_superuser and donation.created_by != request.user:
        messages.error(request, 'No tienes permiso para editar esta donación.')
        return redirect('donations:list')

    if request.method == 'POST':
        form = DonationForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Donación actualizada exitosamente.')
            return redirect('donations:list')
    else:
        form = DonationForm(instance=donation)
    
    return render(request, 'donations/donation_form.html', {
        'form': form,
        'donation': donation,
        'action': 'Editar'
    })

@login_required
def donation_delete(request, pk):
    """
    Vista que permite eliminar una donación.
    Solo permite eliminar al creador o superusuarios.
    """
    donation = get_object_or_404(Donation, pk=pk)
    
    if not request.user.is_superuser and donation.created_by != request.user:
        messages.error(request, 'No tienes permiso para eliminar esta donación.')
        return redirect('donations:list')

    if request.method == 'POST':
        donation.delete()
        messages.success(request, 'Donación eliminada exitosamente.')
        return redirect('donations:list')
    
    return render(request, 'donations/donation_confirm_delete.html', {
        'donation': donation
    })
