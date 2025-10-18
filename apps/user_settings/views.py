# apps/user_settings/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserSettingsForm

@login_required
def profile(request):
    """Vista de perfil/configuración del usuario"""
    if request.method == 'POST':
        form = UserSettingsForm(request.user, request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('user_settings:profile')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserSettingsForm(request.user, instance=request.user)
    return render(request, 'user_settings/profile.html', {'form': form})
