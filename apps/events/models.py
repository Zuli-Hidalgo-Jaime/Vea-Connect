# apps/events/models.py

from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título del evento")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    date = models.DateField(verbose_name="Fecha", blank=True, null=True)
    time = models.TimeField(verbose_name="Hora", blank=True, null=True)
    location = models.CharField(max_length=255, verbose_name="Lugar", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el", blank=True, null=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.title} - {self.date}"
