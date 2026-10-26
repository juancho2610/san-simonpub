# Configuracion del modelo de cuentas para los clientes
from decimal import Decimal

from django.conf import settings
from django.db import models


#Clase metodo de pago
class MetodoPago(models.Model):
    nombre = models.CharField(max_length=40, unique=True)
    activo = models.BooleanField(default=True)
    pide_referencia = models.BooleanField(
        default=False,
        help_text='Muestra un campo para anotar la referencia '
                  '(por ejemplo, en transferencias).')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'método de pago'
        verbose_name_plural = 'métodos de pago'

    def __str__(self):
        return self.nombre

#Clase para la secuencia de los comprobantes
class Secuencia(models.Model):
    """Contador para numerar comprobantes sin saltos (1, 2, 3...)."""
    nombre = models.CharField(max_length=30, unique=True)
    ultimo = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.nombre}: {self.ultimo}'

#Clase de cuenta
class Cuenta(models.Model):
    class Estado(models.TextChoices):
        ABIERTA = 'ABIERTA', 'Abierta'
        SOLICITADA = 'SOLICITADA', 'Cobro solicitado'
        PAGADA = 'PAGADA', 'Pagada'
        ANULADA = 'ANULADA', 'Anulada'

    VIGENTES = [Estado.ABIERTA, Estado.SOLICITADA]

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='cuentas')
    estado = models.CharField(
        max_length=12, choices=Estado.choices, default=Estado.ABIERTA)
    # Lo que el cliente dice que usará (ayuda al personal a prepararse).
    metodo_preferido = models.ForeignKey(
        MetodoPago, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cuentas_preferidas')
    # Lo que realmente se usó al cobrar:
    metodo_pago = models.ForeignKey(
        MetodoPago, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cuentas_pagadas')
    referencia_pago = models.CharField(max_length=60, blank=True)
    numero = models.PositiveIntegerField(
        null=True, blank=True, unique=True,
        help_text='Número consecutivo del comprobante')
    total_cobrado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    cobrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='cuentas_cobradas')
    motivo_anulacion = models.CharField(max_length=200, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    cerrada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada']

    @property
    def total(self):
        """Cuenta ya cerrada: el valor congelado. Abierta: la suma en vivo."""
        if self.total_cobrado is not None:
            return self.total_cobrado
        pedidos = (self.pedidos.exclude(estado='CANCELADO')
                   .prefetch_related('detalles'))
        return sum((p.total for p in pedidos), Decimal('0'))

    def __str__(self):
        return f'Cuenta #{self.pk} - {self.cliente} ({self.get_estado_display()})'
