# apps/documents/forms.py

from django import forms
from .models import Document
from django.core.exceptions import ValidationError
import os

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = '__all__'
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Título del documento"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png,.docx,.pptx,.xls,.xlsx,.txt,.zip"}),
            "description": forms.Textarea(attrs={"class": "form-control", "placeholder": "Descripción", "rows": 2}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            allowed = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.pptx', '.xls', '.xlsx', '.txt', '.zip']
            blocked = ['.exe', '.bat', '.sh', '.js', '.msi', '.cmd', '.scr', '.ps1', '.php', '.py', '.pl']
            if ext in blocked:
                raise ValidationError('No se permite subir archivos ejecutables o peligrosos.')
            if ext not in allowed:
                raise ValidationError('Tipo de archivo no permitido. Solo se permiten: pdf, imágenes, office, txt y zip.')
        return file
