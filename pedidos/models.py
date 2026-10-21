# Create your models here for pedidos in the client.
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from menu.models import Producto

#Clase pedidos modelo base
class Pedido(models.Model):
    class Tipo(models.TextChoices):
        EN_MESA = 'EN_MESA', 'En mesa'
        RECOGER = 'RECOGER', 'Para recoger'
        DOMICILIO = 'DOMICILIO', 'Domicilio'
#Clase estado a nivel de preparacion al realizar el pedido
    class Estado(models.TextChoices):
        RECIBIDO = 'RECIBIDO', 'Recibido'
        EN_PREPARACION = 'EN_PREPARACION', 'En preparación'
        LISTO = 'LISTO', 'Listo'
        EN_CAMINO = 'EN_CAMINO', 'En camino'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='pedidos')
    tipo = models.CharField(max_length=10, choices=Tipo.choices,
                            default=Tipo.EN_MESA)
    mesa = models.PositiveSmallIntegerField(null=True, blank=True)
    direccion_entrega = models.CharField(max_length=200, blank=True)
    telefono_contacto = models.CharField(max_length=20, blank=True)
    notas = models.CharField(max_length=300, blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices,
                              default=Estado.RECIBIDO)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']

    def clean(self):
        errores = {}
        if self.tipo == self.Tipo.EN_MESA and not self.mesa:
            errores['mesa'] = 'Indica el número de mesa.'
        if self.tipo == self.Tipo.DOMICILIO:
            if not self.direccion_entrega:
                errores['direccion_entrega'] = 'La dirección es obligatoria.'
            if not self.telefono_contacto:
                errores['telefono_contacto'] = 'El teléfono es obligatorio.'
        if errores:
            raise ValidationError(errores)

    @property
    def total(self):
        return sum((d.subtotal for d in self.detalles.all()), Decimal('0'))

    def __str__(self):
        return f'Pedido #{self.pk} - {self.get_estado_display()}'

#Clase detalle del pedido muestra el tipo de pedido y su descripcion
class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    # Copias "congeladas" al momento de pedir:
    nombre_producto = models.CharField(max_length=100, blank=True)
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True,
        validators=[MinValueValidator(Decimal('0'))])
    cantidad = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['pedido', 'producto'], name='un_producto_por_pedido'),
        ]

    def save(self, *args, **kwargs):
        # El servidor copia nombre y precio reales. No vienen del navegador.
        if not self.nombre_producto:
            self.nombre_producto = self.producto.nombre
        if self.precio_unitario is None:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return f'{self.cantidad} x {self.nombre_producto}'
