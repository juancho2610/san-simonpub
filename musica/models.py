# Modelo para el sistema de musica
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


#Clase Cancion
class Cancion(models.Model):
    titulo = models.CharField(max_length=120)
    artista = models.CharField(max_length=120)
    archivo = models.FileField(
        upload_to='canciones/',
        validators=[FileExtensionValidator(['mp3', 'ogg', 'wav', 'm4a'])])
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['titulo']
        verbose_name = 'canción'
        verbose_name_plural = 'canciones'
        constraints = [
            models.UniqueConstraint(
                fields=['titulo', 'artista'], name='cancion_unica'),
        ]

    def __str__(self):
        return f'{self.titulo} — {self.artista}'


class SolicitudMusical(models.Model):
    class Estado(models.TextChoices):
        EN_COLA = 'EN_COLA', 'En cola'
        REPRODUCIENDO = 'REPRODUCIENDO', 'Reproduciendo'
        REPRODUCIDA = 'REPRODUCIDA', 'Reproducida'
        OMITIDA = 'OMITIDA', 'Omitida por el personal'
        CANCELADA = 'CANCELADA', 'Cancelada por el cliente'

    cancion = models.ForeignKey(
        Cancion, on_delete=models.PROTECT, related_name='solicitudes')
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='solicitudes_musicales')
    # El pedido que habilitó esta solicitud (queda como evidencia).
    pedido = models.ForeignKey(
        'pedidos.Pedido', on_delete=models.PROTECT,
        related_name='solicitudes_musicales')
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.EN_COLA)
    creada = models.DateTimeField(auto_now_add=True)
    inicio = models.DateTimeField(null=True, blank=True)
    fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['creada']
        verbose_name = 'solicitud musical'
        verbose_name_plural = 'solicitudes musicales'

    def __str__(self):
        return f'{self.cancion} ({self.get_estado_display()})'

