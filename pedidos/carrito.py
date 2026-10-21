#clase de carrito para el sistema de pedidos
from menu.models import Producto

SESSION_KEY = 'carrito'
MAX_CANTIDAD = 20 #cantidad maxima por producto, para evitar errores de dedo o clicks o abusos al agregar productos.


#Clase Carrito
class Carrito:
    """Guarda {id_producto: cantidad} en la sesión. Nunca guarda precios."""

    def __init__(self, request):
        self.session = request.session
        self.items = self.session.setdefault(SESSION_KEY, {})

    def _guardar(self):
        self.session.modified = True

    def agregar(self, producto, cantidad=1):
        clave = str(producto.pk)
        nueva = self.items.get(clave, 0) + cantidad
        self.items[clave] = max(1, min(nueva, MAX_CANTIDAD))
        self._guardar()

    def fijar(self, producto_id, cantidad):
        clave = str(producto_id)
        if clave not in self.items:
            return
        if cantidad <= 0:
            del self.items[clave]
        else:
            self.items[clave] = min(cantidad, MAX_CANTIDAD)
        self._guardar()

    def quitar(self, producto_id):
        self.items.pop(str(producto_id), None)
        self._guardar()

    def vaciar(self):
        self.items.clear()
        self._guardar()

    def lineas(self):
        """Líneas con precios REALES de hoy. Ignora productos ya no disponibles."""
        ids = [int(k) for k in self.items]
        productos = Producto.objects.filter(
            pk__in=ids, disponible=True, categoria__activa=True)
        lineas = []
        for p in productos:
            cantidad = self.items[str(p.pk)]
            lineas.append({
                'producto': p,
                'cantidad': cantidad,
                'subtotal': p.precio * cantidad,
            })
        return lineas
