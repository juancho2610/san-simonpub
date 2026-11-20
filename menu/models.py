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
    precio_desde = models.BooleanField(
        'mostrar "desde" en el precio', default=False,
        help_text='Para platos con precio variable (ej. Tomahawk)')
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

    @property
    def tiene_opciones(self):
        """True si hay opciones disponibles para elegir (usa el prefetch si existe)."""
        return any(o.disponible for g in self.grupos.all() for o in g.opciones.all())

#Clase Grupo de opciones para adicionales de proteina
class GrupoOpciones(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='grupos')
    nombre = models.CharField(max_length=60)
    obligatorio = models.BooleanField(
        default=False, help_text='Si está marcado, el cliente debe elegir al menos una')
    max_selecciones = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)],
        help_text='1 = una sola opción; más de 1 = puede elegir varias')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'grupo de opciones'
        verbose_name_plural = 'grupos de opciones'
        constraints = [
            models.UniqueConstraint(
                fields=['producto', 'nombre'], name='grupo_unico_por_producto'),
        ]

    def __str__(self):
        return f'{self.producto.nombre} - {self.nombre}'

    @property
    def opciones_disponibles(self):
        return [o for o in self.opciones.all() if o.disponible]


#Opción dentro de un grupo, con un precio extra como adicional
class Opcion(models.Model):
    grupo = models.ForeignKey(
        GrupoOpciones, on_delete=models.CASCADE, related_name='opciones')
    nombre = models.CharField(max_length=80)
    precio_extra = models.DecimalField(
        'precio extra (COP)', max_digits=10, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))])
    disponible = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'opción'
        verbose_name_plural = 'opciones'
        constraints = [
            models.UniqueConstraint(
                fields=['grupo', 'nombre'], name='opcion_unica_por_grupo'),
        ]

    def __str__(self):
        return f'{self.nombre} (+${self.precio_extra:,.0f})'
