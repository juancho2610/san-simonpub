#Creacion de los modelos
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

# Create your models here.
#Clase categoria
class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    orden = models.PositiveSmallIntegerField(
        default=0, help_text='Número menor = aparece primero en el menú')
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre

#Clase productos
class Producto(models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos')
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=300, blank=True)
    precio = models.DecimalField(
        'precio (COP)', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))])
    disponible = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='productos/', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['categoria__orden', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['categoria', 'nombre'], name='producto_unico_por_categoria'),
        ]

    def __str__(self):
        return f'{self.nombre} (${self.precio:,.0f})'
