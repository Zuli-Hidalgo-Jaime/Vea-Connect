from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "date", "time", "location", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del evento"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "text", "id": "id_date", "autocomplete": "off"}),
            "time": forms.TimeInput(attrs={"class": "form-control", "type": "text", "id": "id_time", "autocomplete": "off"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ubicación"}),
            "description": forms.Textarea(attrs={"class": "form-control", "placeholder": "Descripción", "rows": 2}),
        } 