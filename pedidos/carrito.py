#clase de carrito para el sistema de pedidos
from decimal import Decimal

from menu.models import Producto
from menu.opciones import validar_seleccion

SESSION_KEY = 'carrito'
MAX_CANTIDAD = 20 #cantidad maxima por producto, para evitar errores de dedo o clicks o abusos al agregar productos.


def _clave(producto_id, opciones_ids=()):
    """'12' si no hay opciones; '12:3-5' si eligió las opciones 3 y 5."""
    ids = sorted(set(int(i) for i in opciones_ids))
    if not ids:
        return str(producto_id)
    return f'{producto_id}:' + '-'.join(str(i) for i in ids)


def _separar(clave):
    """'12:3-5' -> (12, [3, 5]). Devuelve None si la clave no es válida."""
    try:
        base, _, resto = str(clave).partition(':')
        ids = [int(x) for x in resto.split('-')] if resto else []
        return int(base), ids
    except ValueError:
        return None


#Clase Carrito
class Carrito:
    """Guarda {clave: cantidad} en la sesión. Nunca guarda precios."""

    def __init__(self, request):
        self.session = request.session
        self.items = self.session.setdefault(SESSION_KEY, {})

    def _guardar(self):
        self.session.modified = True

    def agregar(self, producto, cantidad=1, opciones=()):
        clave = _clave(producto.pk, [o.pk for o in opciones])
        nueva = self.items.get(clave, 0) + cantidad
        self.items[clave] = max(1, min(nueva, MAX_CANTIDAD))
        self._guardar()

    def fijar(self, clave, cantidad):
        clave = str(clave)
        if clave not in self.items:
            return
        if cantidad <= 0:
            del self.items[clave]
        else:
            self.items[clave] = min(cantidad, MAX_CANTIDAD)
        self._guardar()

    def quitar(self, clave):
        self.items.pop(str(clave), None)
        self._guardar()

    def vaciar(self):
        self.items.clear()
        self._guardar()

    def lineas(self):
        """Líneas con precios REALES de hoy. Ignora lo que ya no esté disponible."""
        lineas = []
        for clave, cantidad in list(self.items.items()):
            partes = _separar(clave)
            if partes is None:
                continue
            producto_id, ids = partes
            producto = Producto.objects.filter(
                pk=producto_id, disponible=True, categoria__activa=True).first()
            if producto is None:
                continue
            opciones, texto, error = validar_seleccion(producto, ids)
            if error:
                continue
            extra = sum((o.precio_extra for o in opciones), Decimal('0'))
            unitario = producto.precio + extra
            lineas.append({
                'clave': clave,
                'producto': producto,
                'opciones': opciones,
                'opciones_texto': texto,
                'cantidad': cantidad,
                'precio_unitario': unitario,
                'subtotal': unitario * cantidad,
            })
        return lineas
