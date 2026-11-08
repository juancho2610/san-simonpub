from django.conf import settings
from django.db import models


class Interaccion(models.Model):
    class Origen(models.TextChoices):
        IA = 'IA', 'Asistente con IA'
        RESPALDO = 'RESPALDO', 'Respuesta fija'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='interacciones')
    tema = models.CharField(max_length=20, blank=True)
    pregunta = models.CharField(max_length=400, blank=True)
    respuesta = models.TextField(blank=True)
    origen = models.CharField(max_length=10, choices=Origen.choices)
    tokens_entrada = models.PositiveIntegerField(default=0)
    tokens_salida = models.PositiveIntegerField(default=0)
    creada = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-creada']
        verbose_name = 'interacción'
        verbose_name_plural = 'interacciones'

    def __str__(self):
        return f'{self.usuario} - {self.get_origen_display()} ({self.creada:%d/%m %H:%M})'
