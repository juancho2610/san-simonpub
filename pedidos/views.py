#Clase para la vista del sistema de pedidos nivel de cliente
import csv

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Sum, Q
from django.utils import timezone
from django.http import HttpResponse

from datetime import datetime, time, timedelta

from musica.models import SolicitudMusical
from usuarios.models import Rol
from usuarios.views import rol_requerido
from menu.models import Producto

from .forms import PedidoForm
from .models import Calificacion, DetallePedido, Pedido
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


@rol_requerido(Rol.ADMIN)
def estadisticas(request):
    # Rangos de fecha explícitos: funcionan bien con MySQL y la zona horaria.
    hoy = timezone.localdate()
    inicio_hoy = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_hoy = inicio_hoy + timedelta(days=1)
    inicio_semana = inicio_hoy - timedelta(days=6)  # hoy + 6 días anteriores

    valor_linea = ExpressionWrapper(
        F('precio_unitario') * F('cantidad'),
        output_field=DecimalField(max_digits=14, decimal_places=2))

    cancelado = Pedido.Estado.CANCELADO
    pedidos_hoy = Pedido.objects.filter(creado__gte=inicio_hoy, creado__lt=fin_hoy)

    lineas_hoy = DetallePedido.objects.filter(
        pedido__creado__gte=inicio_hoy, pedido__creado__lt=fin_hoy
    ).exclude(pedido__estado=cancelado)

    ventas_hoy = lineas_hoy.aggregate(t=Sum(valor_linea))['t'] or 0
    num_validos = pedidos_hoy.exclude(estado=cancelado).count()

    por_estado = [
        {'estado': Pedido.Estado(f['estado']).label, 'n': f['n']}
        for f in pedidos_hoy.values('estado').annotate(n=Count('id')).order_by('estado')
    ]
    por_tipo = [
        {'tipo': Pedido.Tipo(f['tipo']).label, 'n': f['n']}
        for f in pedidos_hoy.exclude(estado=cancelado)
        .values('tipo').annotate(n=Count('id')).order_by('tipo')
    ]

    top_productos = (
        DetallePedido.objects
        .filter(pedido__creado__gte=inicio_semana, pedido__creado__lt=fin_hoy)
        .exclude(pedido__estado=cancelado)
        .values('nombre_producto')
        .annotate(unidades=Sum('cantidad'), ventas=Sum(valor_linea))
        .order_by('-unidades', 'nombre_producto')[:10]
    )

    contexto = {
        'hoy': hoy,
        'num_pedidos': num_validos,
        'ventas_hoy': ventas_hoy,
        'ticket_promedio': (ventas_hoy / num_validos) if num_validos else 0,
        'por_estado': por_estado,
        'por_tipo': por_tipo,
        'top_productos': top_productos,
	'top_canciones': _top_canciones(inicio_semana, fin_hoy),
	'calificaciones': _calificaciones_por_producto(
            fin_hoy - timedelta(days=30), fin_hoy),
    }
    return render(request, 'pedidos/estadisticas.html', contexto)


def _rango_semana():
    hoy = timezone.localdate()
    inicio_hoy = timezone.make_aware(datetime.combine(hoy, time.min))
    return inicio_hoy - timedelta(days=6), inicio_hoy + timedelta(days=1)


def _top_productos(inicio, fin, limite=10):
    valor = ExpressionWrapper(
        F('precio_unitario') * F('cantidad'),
        output_field=DecimalField(max_digits=14, decimal_places=2))
    return (
        DetallePedido.objects
        .filter(pedido__creado__gte=inicio, pedido__creado__lt=fin)
        .exclude(pedido__estado=Pedido.Estado.CANCELADO)
        .values('nombre_producto')
        .annotate(unidades=Sum('cantidad'), ventas=Sum(valor))
        .order_by('-unidades', 'nombre_producto')[:limite]
    )


def _top_canciones(inicio, fin, limite=10):
    S = SolicitudMusical
    return (
        S.objects
        .filter(creada__gte=inicio, creada__lt=fin)
        .exclude(estado=S.Estado.CANCELADA)
        .values('cancion_id', 'cancion__titulo', 'cancion__artista')
        .annotate(veces=Count('id'),
                  sonadas=Count('id', filter=Q(estado=S.Estado.REPRODUCIDA)))
        .order_by('-veces', 'cancion__titulo')[:limite]
    )


def _csv_seguro(valor):
    texto = str(valor)
    return "'" + texto if texto[:1] in ('=', '+', '-', '@', '\t', '\r') else texto


@rol_requerido(Rol.ADMIN)
def reporte_semanal_csv(request):
    inicio, fin = _rango_semana()
    respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
    respuesta['Content-Disposition'] = (
        f'attachment; filename="reporte_semanal_{timezone.localdate()}.csv"')
    respuesta.write('\ufeff')  # para que Excel muestre bien las tildes
    escritor = csv.writer(respuesta)
    escritor.writerow(['Periodo', f'{inicio.date()} a {(fin - timedelta(days=1)).date()}'])
    escritor.writerow([])
    escritor.writerow(['Tipo', 'Nombre', 'Unidades o veces pedidas', 'Ventas COP o veces sonadas'])
    for p in _top_productos(inicio, fin, limite=50):
        escritor.writerow(['Producto', _csv_seguro(p['nombre_producto']),
                           p['unidades'], p['ventas']])
    for c in _top_canciones(inicio, fin, limite=50):
        nombre = f"{c['cancion__titulo']} — {c['cancion__artista']}"
        escritor.writerow(['Canción', _csv_seguro(nombre), c['veces'], c['sonadas']])

    escritor.writerow([])
    escritor.writerow(['Calificaciones de los últimos 30 días'])
    escritor.writerow(['Tipo', 'Producto', 'Promedio de estrellas',
                       'Cantidad de calificaciones'])
    for c in _calificaciones_por_producto(fin - timedelta(days=30), fin):
        escritor.writerow(['Calificación',
                           _csv_seguro(c['detalle__producto__nombre']),
                           round(c['promedio'], 2), c['cantidad']])
    return respuesta


@require_POST
@rol_requerido(Rol.CLIENTE)
def calificar(request, pk):
    with transaction.atomic():
        # Bloqueamos el pedido: dos envíos a la vez no pueden duplicar nada.
        # Filtrar por cliente impide calificar pedidos ajenos.
        pedido = get_object_or_404(
            Pedido.objects.select_for_update(), pk=pk, cliente=request.user)

        if pedido.estado != Pedido.Estado.ENTREGADO:
            messages.error(
                request, 'Solo puedes calificar pedidos ya entregados.')
            return redirect('detalle_pedido', pk=pedido.pk)

        ya_calificados = set(
            Calificacion.objects.filter(detalle__pedido=pedido)
            .values_list('detalle_id', flat=True))

        nuevas = []
        for d in pedido.detalles.all():
            if d.pk in ya_calificados:
                continue
            bruto = request.POST.get(f'estrellas_{d.pk}', '').strip()
            if not bruto:
                continue  # el cliente puede calificar solo algunos productos
            if bruto not in ('1', '2', '3', '4', '5'):
                messages.error(request, 'El puntaje debe ser de 1 a 5.')
                return redirect('detalle_pedido', pk=pedido.pk)
            comentario = request.POST.get(f'comentario_{d.pk}', '').strip()
            if len(comentario) > 200:
                messages.error(
                    request, 'El comentario no puede pasar de 200 caracteres.')
                return redirect('detalle_pedido', pk=pedido.pk)
            nuevas.append(Calificacion(
                detalle=d, estrellas=int(bruto), comentario=comentario))

        if not nuevas:
            messages.warning(request, 'Elige al menos un puntaje.')
            return redirect('detalle_pedido', pk=pedido.pk)

        Calificacion.objects.bulk_create(nuevas)

    messages.success(request, '¡Gracias por tu opinión!')
    return redirect('detalle_pedido', pk=pedido.pk)



def _calificaciones_por_producto(inicio, fin):
    return (
        Calificacion.objects
        .filter(creada__gte=inicio, creada__lt=fin)
        .values('detalle__producto_id', 'detalle__producto__nombre')
        .annotate(promedio=Avg('estrellas'), cantidad=Count('id'))
        .order_by('-promedio', '-cantidad', 'detalle__producto__nombre')
    )
