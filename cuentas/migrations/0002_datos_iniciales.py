from django.db import migrations

METODOS = [
    ('Efectivo', 1, False),
    ('Datáfono', 2, False),
    ('Transferencia', 3, True),
]


def cargar(apps, schema_editor):
    MetodoPago = apps.get_model('cuentas', 'MetodoPago')
    Secuencia = apps.get_model('cuentas', 'Secuencia')
    for nombre, orden, pide_referencia in METODOS:
        MetodoPago.objects.get_or_create(
            nombre=nombre,
            defaults={'orden': orden, 'pide_referencia': pide_referencia})
    Secuencia.objects.get_or_create(nombre='comprobante', defaults={'ultimo': 0})


class Migration(migrations.Migration):

    dependencies = [
        ('cuentas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
