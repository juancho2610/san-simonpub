# Modelo para el sistema de musica
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


#Clase Cancion
class Cancion(models.Model):
    titulo = models.CharField(max_length=120)
    artista = models.CharField(max_length=120)
    archivo = models.FileField(
        upload_to='canciones/', blank=True,
        validators=[FileExtensionValidator(['mp3', 'ogg', 'wav', 'm4a'])])
    # Si viene de YouTube: el id del video (11 caracteres).
    youtube_id = models.CharField(
        max_length=20, unique=True, null=True, blank=True)
    duracion_segundos = models.PositiveIntegerField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['titulo']
        verbose_name = 'canción'
        verbose_name_plural = 'canciones'

    @property
    def es_youtube(self):
        return bool(self.youtube_id)

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.archivo and not self.youtube_id:
            raise ValidationError(
                'La canción necesita un archivo o un id de YouTube.')

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



class BusquedaYoutube(models.Model):
    """Una consulta real hecha a YouTube. Sirve de caché y de contador de cupo.
    Se borra a los pocos días (política de datos de la API: máximo 30)."""
    consulta = models.CharField(max_length=100, db_index=True)
    resultados = models.JSONField(default=list)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='busquedas_youtube')
    creada = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-creada']
        verbose_name = 'búsqueda en YouTube'
        verbose_name_plural = 'búsquedas en YouTube'

    def __str__(self):
        return f'{self.consulta} ({self.creada:%Y-%m-%d %H:%M})'
