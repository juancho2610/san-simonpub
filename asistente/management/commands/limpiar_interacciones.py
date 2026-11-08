from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from asistente.models import Interaccion


class Command(BaseCommand):
    help = 'Borra las interacciones del asistente más viejas que el periodo de retención.'

    def handle(self, *args, **options):
        limite = timezone.now() - timedelta(days=settings.ASISTENTE_RETENCION_DIAS)
        borradas, _ = Interaccion.objects.filter(creada__lt=limite).delete()
        self.stdout.write(self.style.SUCCESS(f'Interacciones borradas: {borradas}'))
