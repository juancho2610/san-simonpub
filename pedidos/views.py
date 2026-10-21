#Clase para la vista del sistema de pedidos nivel de cliente
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction


from usuarios.models import Rol
from usuarios.views import rol_requerido
from menu.models import Producto

from .forms import PedidoForm
from .models import DetallePedido, Pedido
from .carrito import Carrito

#Vista Carrito
def ver_carrito(request):
    lineas = Carrito(request).lineas()
    total = sum(l['subtotal'] for l in lineas)
    return render(request, 'pedidos/carrito.html',
                  {'lineas': lineas, 'total': total})


@require_POST
def agregar(request, pk):
    producto = get_object_or_404(
        Producto, pk=pk, disponible=True, categoria__activa=True)
    Carrito(request).agregar(producto)
    messages.success(request, f'Agregaste "{producto.nombre}" al carrito.')
    return redirect('menu')


@require_POST
def actualizar(request, pk):
    try:
        cantidad = int(request.POST.get('cantidad', ''))
    except ValueError:
        return redirect('ver_carrito')
    Carrito(request).fijar(pk, cantidad)
    return redirect('ver_carrito')


@require_POST
def quitar(request, pk):
    Carrito(request).quitar(pk)
    return redirect('ver_carrito')


@require_POST
def vaciar(request):
    Carrito(request).vaciar()
    return redirect('ver_carrito')


@rol_requerido(Rol.CLIENTE)
def confirmar(request):
    carrito = Carrito(request)
    lineas = carrito.lineas()
    if not lineas:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('menu')
    total = sum(l['subtotal'] for l in lineas)

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                pedido = form.save(commit=False)
                pedido.cliente = request.user
                pedido.save()
                for l in lineas:
                    DetallePedido.objects.create(
                        pedido=pedido, producto=l['producto'],
                        cantidad=l['cantidad'])
            carrito.vaciar()
            messages.success(request, 'Tu pedido fue recibido.')
            return redirect('detalle_pedido', pk=pedido.pk)
    else:
        form = PedidoForm(
            initial={'telefono_contacto': request.user.telefono})

    return render(request, 'pedidos/confirmar.html',
                  {'form': form, 'lineas': lineas, 'total': total})


@login_required
def mis_pedidos(request):
    pedidos = request.user.pedidos.all()
    return render(request, 'pedidos/mis_pedidos.html', {'pedidos': pedidos})


@login_required
def detalle_pedido(request, pk):
    # Filtrar por cliente impide ver pedidos ajenos.
    pedido = get_object_or_404(Pedido, pk=pk, cliente=request.user)
    return render(request, 'pedidos/detalle_pedido.html', {'pedido': pedido})
