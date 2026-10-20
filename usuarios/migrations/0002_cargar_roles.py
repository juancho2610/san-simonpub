from django.db import migrations

ROLES = [
    ('ADMIN', 'Administrador', 'Gestiona usuarios, menú, reportes y todo el sistema'),
    ('SERVICIO', 'Personal de servicio', 'Atiende mesas, gestiona pedidos y facturación'),
    ('COCINA_BAR', 'Cocina / Bar', 'Prepara pedidos y actualiza su estado'),
    ('CLIENTE', 'Cliente', 'Consulta el menú, pide, solicita canciones y usa el chat'),
]


def cargar_roles(apps, schema_editor):
    Rol = apps.get_model('usuarios', 'Rol')
    for codigo, nombre, descripcion in ROLES:
        Rol.objects.get_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'descripcion': descripcion},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cargar_roles, migrations.RunPython.noop),
    ]
