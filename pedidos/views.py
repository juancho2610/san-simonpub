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



@rol_requerido(Rol.ADMIN, Rol.SERVICIO, Rol.COCINA_BAR)
def tablero(request):
    codigo = request.user.rol.codigo
    activos = (
        Pedido.objects
        .exclude(estado__in=[Pedido.Estado.ENTREGADO, Pedido.Estado.CANCELADO])
        .select_related('cliente')
        .prefetch_related('detalles')
    )
    if codigo == Rol.COCINA_BAR:
        activos = activos.filter(estado__in=[
            Pedido.Estado.RECIBIDO, Pedido.Estado.EN_PREPARACION])
    pedidos = list(activos.order_by('creado'))  # el más antiguo primero
    for p in pedidos:
        p.opciones = p.estados_permitidos(codigo)
    return render(request, 'pedidos/tablero.html', {'pedidos': pedidos})


@require_POST
@rol_requerido(Rol.ADMIN, Rol.SERVICIO, Rol.COCINA_BAR)
def cambiar_estado(request, pk):
    nuevo = request.POST.get('estado')
    with transaction.atomic():
        # select_for_update bloquea el pedido mientras se decide el cambio
        pedido = get_object_or_404(Pedido.objects.select_for_update(), pk=pk)
        permitidos = [e for e, _ in pedido.estados_permitidos(request.user.rol.codigo)]
        if nuevo in permitidos:
            pedido.estado = nuevo
            pedido.save(update_fields=['estado', 'actualizado'])
            messages.success(
                request, f'Pedido #{pedido.pk}: {pedido.get_estado_display()}.')
        else:
            messages.error(
                request, 'Ese cambio no es posible (quizá un compañero ya lo hizo).')
    return redirect('tablero_pedidos')
