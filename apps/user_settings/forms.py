from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserSettingsForm(forms.ModelForm):
    current_password = forms.CharField(
        label=_('Contraseña actual'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    new_password = forms.CharField(
        label=_('Nueva contraseña'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': _('Nombre'),
            'last_name': _('Apellido'),
            'email': _('Correo electrónico'),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError(_('La contraseña actual es incorrecta.'))
        return current_password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise forms.ValidationError(_('Este correo electrónico ya está en uso.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user 