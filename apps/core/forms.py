from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


# -------------------------------
# Formulario de Registro (Signup)
# -------------------------------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "username")
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Tu nombre'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Tu apellido'}),
            'username': forms.TextInput(attrs={'placeholder': 'Nombre de usuario (opcional)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        
        if not username:
            cleaned_data['username'] = email.split('@')[0] if email else ''
        
        return cleaned_data


# ---------------------------------------------
# Formulario de Inicio de Sesión (Login Custom)
# ---------------------------------------------
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Correo electrónico"),
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'placeholder': 'correo@ejemplo.com',
            'class': 'form-control',
        })
    )
    password = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Tu contraseña',
            'class': 'form-control',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.lower().strip()
        return username
