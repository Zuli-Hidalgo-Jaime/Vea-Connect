# apps/events/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Event
from django.contrib.auth.decorators import login_required
from .forms import EventForm

@login_required
def event_list(request):
    """Vista que lista los eventos"""
    events = Event.objects.all()
    return render(request, 'events/events.html', {'events': events})

@login_required
def event_create(request):
    """Vista para crear un evento"""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento creado correctamente.')
            return redirect('events:events')
    else:
        form = EventForm()
    return render(request, 'events/create.html', {'form': form, 'edit': False})

@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento actualizado correctamente.')
            return redirect('events:events')
    else:
        form = EventForm(instance=event)
    return render(request, 'events/create.html', {'form': form, 'edit': True})

@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Evento eliminado correctamente.')
        return redirect('events:events')
    return render(request, 'events/confirm_delete.html', {'event': event})
