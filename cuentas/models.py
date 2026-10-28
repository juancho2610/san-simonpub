# Configuracion del modelo de cuentas para los clientes
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

#Clase para el metodo de pago
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

#Clase Secuencia de comprobantes de los pedidos
class Secuencia(models.Model):
    """Contador para numerar comprobantes sin saltos (1, 2, 3...)."""
    nombre = models.CharField(max_length=30, unique=True)
    ultimo = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.nombre}: {self.ultimo}'

#Clase Cuentas
class Cuenta(models.Model):
    class Estado(models.TextChoices):
        ABIERTA = 'ABIERTA', 'Abierta'
        PENDIENTE = 'PENDIENTE', 'Pendiente de pago'
        PAGADA = 'PAGADA', 'Pagada'
        ANULADA = 'ANULADA', 'Anulada'

    # Solo una cuenta ABIERTA acumula pedidos nuevos. Las pendientes no.
    VIGENTES = [Estado.ABIERTA]

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='cuentas')
    estado = models.CharField(
        max_length=12, choices=Estado.choices, default=Estado.ABIERTA)
    numero = models.PositiveIntegerField(
        null=True, blank=True, unique=True,
        help_text='Número consecutivo del comprobante (solo cuentas pagadas)')
    # Total congelado al cerrar la cuenta (pagada o pendiente).
    total_cobrado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    cobrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='cuentas_cobradas',
        help_text='Quien cerró la cuenta (al cobrar o al dejarla pendiente)')
    motivo_anulacion = models.CharField(max_length=200, blank=True)
    anulada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='cuentas_anuladas')
    anulada = models.DateTimeField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    cerrada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada']

    @property
    def total(self):
        """Cerrada: el valor congelado. Abierta: la suma en vivo."""
        if self.total_cobrado is not None:
            return self.total_cobrado
        pedidos = (self.pedidos.exclude(estado='CANCELADO')
                   .prefetch_related('detalles'))
        return sum((p.total for p in pedidos), Decimal('0'))

    @property
    def pagado(self):
        return sum((p.monto for p in self.pagos.all()), Decimal('0'))

    @property
    def saldo(self):
        return self.total - self.pagado

    def __str__(self):
        return f'Cuenta #{self.pk} - {self.cliente} ({self.get_estado_display()})'

#Clase de PAGO
class Pago(models.Model):
    cuenta = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name='pagos')
    metodo = models.ForeignKey(
        MetodoPago, on_delete=models.PROTECT, related_name='pagos')
    monto = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))])
    referencia = models.CharField(max_length=60, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='pagos_registrados')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gt=0), name='pago_monto_positivo'),
        ]

    def __str__(self):
        return f'${self.monto:,.0f} - {self.metodo} (cuenta #{self.cuenta_id})'
