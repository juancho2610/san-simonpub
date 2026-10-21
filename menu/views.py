#vistas del menu
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Producto
# Create your views here.
#vista del menu para el cliente
def menu_cliente(request):
    # Solo categorías activas y, dentro de ellas, productos disponibles.
    productos = Producto.objects.filter(disponible=True)
    categorias = (
        Categoria.objects.filter(activa=True)
        .prefetch_related(Prefetch('productos', queryset=productos))
    )
    # Ocultamos categorías que quedaron sin productos disponibles.
    categorias = [c for c in categorias if c.productos.all()]
    return render(request, 'menu/menu_cliente.html', {'categorias': categorias})

#vista del detalle del producto
def detalle_producto(request, pk):
    producto = get_object_or_404(
        Producto, pk=pk, disponible=True, categoria__activa=True)
    return render(request, 'menu/detalle_producto.html', {'producto': producto})
