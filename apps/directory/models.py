# apps/directory/models.py

from django.db import models

class Contact(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="Nombre")
    last_name = models.CharField(max_length=50, verbose_name="Apellido")
    role = models.CharField(max_length=100, verbose_name="Rol", blank=True, null=True)
    ministry = models.CharField(max_length=150, verbose_name="Ministerio")
    contact = models.CharField(max_length=100, verbose_name="Contacto")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return "Sin nombre"

    class Meta:
        verbose_name = "Contacto"
        verbose_name_plural = "Contactos"
        ordering = ['last_name', 'first_name']
