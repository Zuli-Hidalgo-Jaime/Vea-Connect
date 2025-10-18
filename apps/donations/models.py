from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db.models import ObjectDoesNotExist

User = get_user_model()

class DonationType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_('Nombre del tipo de donación'))
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Tipo de Donación"
        verbose_name_plural = "Tipos de Donación"

class Donation(models.Model):
    TYPE_CHOICES = [
        ('monetaria', _('Monetaria')),
        ('especie', _('En especie')),
        ('medicamentos', _('Medicamentos')),
        ('voluntariado', _('Voluntariado')),
        ('otros', _('Otros')),
    ]

    METHOD_CHOICES = [
        ('deposito', 'Depósito bancario'),
        ('transferencia', 'Transferencia electrónica'),
        ('relaciones_publicas', 'Mesa de Relaciones Públicas'),
        ('ministerio', 'Encargado de Ministerio'),
        ('entrega_directa', 'Entrega directa en instalaciones'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name=_('Título')
    )
    donation_type = models.ForeignKey(
        'DonationType',
        on_delete=models.CASCADE,
        verbose_name=_('Tipo de donación')
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    method = models.CharField(
        max_length=100,
        choices=METHOD_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Método de pago')
    )
    entity = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Entidad')
    )
    bank = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Banco')
    )
    clabe = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('CLABE')
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Ubicación')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Donación"
        verbose_name_plural = "Donaciones"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title or self.get_donation_type_display()} - {self.created_at.strftime('%d/%m/%Y')}"
    
    def clean(self):
        if self.amount is not None and self.amount < 0:
            raise ValidationError("El monto de la donación no puede ser negativo.")
        super().clean()
    
    def save(self, *args, **kwargs):
        """Validar antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)
        