from django.urls import reverse

CLAVE_CARRITO = 'carrito'

INICIO = ('Inicio', 'inicio', (
    'inicio', 'panel_cliente', 'panel_servicio', 'panel_cocina', 'panel_admin'))

SECCIONES = {
    'ANONIMO': [
        ('Menú', 'menu', ('menu', 'detalle_producto')),
        ('Carrito', 'ver_carrito', ('ver_carrito', 'confirmar_pedido')),
        ('Ingresar', 'login', ('login', 'registro')),
    ],
    'CLIENTE': [
        INICIO,
        ('Menú', 'menu', ('menu', 'detalle_producto')),
        ('Música', 'catalogo_musical', ('catalogo_musical',)),
        ('Pedidos', 'mis_pedidos', ('mis_pedidos', 'detalle_pedido', 'comprobante')),
        ('Carrito', 'ver_carrito', ('ver_carrito', 'confirmar_pedido')),
    ],
    'SERVICIO': [
        INICIO,
        ('Pedidos', 'tablero_pedidos', ('tablero_pedidos',)),
        ('Cuentas', 'cuentas_lista', ('cuentas_lista', 'cuenta_detalle', 'comprobante')),
        ('Música', 'reproductor', ('reproductor',)),
    ],
    'COCINA_BAR': [
        INICIO,
        ('Pedidos', 'tablero_pedidos', ('tablero_pedidos',)),
    ],
    'ADMIN': [
        INICIO,
        ('Pedidos', 'tablero_pedidos', ('tablero_pedidos',)),
        ('Cuentas', 'cuentas_lista', ('cuentas_lista', 'cuenta_detalle', 'comprobante')),
        ('Música', 'reproductor', ('reproductor',)),
        ('Estadísticas', 'estadisticas', ('estadisticas',)),
    ],
}


def _cantidad_carrito(request):
    try:
        return sum(int(c) for c in request.session.get(CLAVE_CARRITO, {}).values())
    except (TypeError, ValueError):
        return 0


def navegacion(request):
    usuario = request.user
    if not usuario.is_authenticated:
        clave = 'ANONIMO'
    else:
        clave = usuario.rol.codigo if usuario.rol else 'CLIENTE'
    match = request.resolver_match
    actual = match.url_name if match else ''

    items = []
    for etiqueta, nombre_url, activos in SECCIONES.get(clave, SECCIONES['CLIENTE']):
        items.append({
            'etiqueta': etiqueta,
            'url': reverse(nombre_url),
            'activo': actual in activos,
            'es_inicio': nombre_url == 'inicio',
            'contador': _cantidad_carrito(request) if nombre_url == 'ver_carrito' else 0,
        })
    return {'nav_items': items}
