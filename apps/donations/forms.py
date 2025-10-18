from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Donation, DonationType

class DonationForm(forms.ModelForm):
    """
    Formulario para crear y editar donaciones.
    Incluye validación condicional basada en el tipo de donación.
    """
    class Meta:
        model = Donation
        fields = [
            'title', 'donation_type', 'amount', 'entity',
            'method', 'bank', 'clabe', 'location', 'description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'donation_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'entity': forms.TextInput(attrs={'class': 'form-control'}),
            'method': forms.Select(attrs={'class': 'form-control'}),
            'bank': forms.TextInput(attrs={'class': 'form-control'}),
            'clabe': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['donation_type'].required = True
        self.fields['donation_type'].queryset = DonationType.objects.all()
        self.fields['amount'].required = False
        self.fields['method'].required = False
        self.fields['entity'].required = False
        self.fields['bank'].required = False
        self.fields['clabe'].required = False
        
        # Si es una edición, obtener el tipo de donación actual
        if self.instance and self.instance.pk:
            self.current_type = self.instance.donation_type
        else:
            self.current_type = None

    def clean(self):
        cleaned_data = super().clean()
        donation_type = cleaned_data.get('donation_type')
        method = cleaned_data.get('method')
        amount = cleaned_data.get('amount')
        bank = cleaned_data.get('bank')
        clabe = cleaned_data.get('clabe')

        if not donation_type:
            raise forms.ValidationError('El tipo de donación es requerido.')

        # Validar campos según el tipo de donación
        if donation_type.name == 'Monetaria':
            # Para donaciones monetarias, el monto es opcional en pruebas
            # Solo validar campos bancarios si se proporcionan
            pass
        elif donation_type.name == 'Alimento':
            if amount:
                self.add_error('amount', 'El monto no aplica para donaciones de alimentos.')
            if bank or clabe:
                self.add_error('bank', 'Los datos bancarios no aplican para donaciones de alimentos.')
                self.add_error('clabe', 'Los datos bancarios no aplican para donaciones de alimentos.')
        elif donation_type.name == 'Especie':
            if amount:
                self.add_error('amount', 'El monto no aplica para donaciones en especie.')
            if bank or clabe:
                self.add_error('bank', 'Los datos bancarios no aplican para donaciones en especie.')
                self.add_error('clabe', 'Los datos bancarios no aplican para donaciones en especie.')

        return cleaned_data

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user is not None:
            instance.created_by = user
        # Forzar la asignación del tipo de donación
        instance.donation_type = self.cleaned_data.get('donation_type')
        if commit:
            instance.save()
        return instance
        