#URL de pedidos para el usuario
from django.urls import path

from . import views

urlpatterns = [
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:pk>/', views.agregar, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:pk>/', views.actualizar, name='actualizar_carrito'),
    path('carrito/quitar/<int:pk>/', views.quitar, name='quitar_del_carrito'),
    path('carrito/vaciar/', views.vaciar, name='vaciar_carrito'),
    path('pedido/confirmar/', views.confirmar, name='confirmar_pedido'),
    path('pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('pedidos/<int:pk>/', views.detalle_pedido, name='detalle_pedido'),
    path('personal/pedidos/', views.tablero, name='tablero_pedidos'),
    path('personal/pedidos/<int:pk>/estado/', views.cambiar_estado, name='cambiar_estado'),
    path('administracion/estadisticas/', views.estadisticas, name='estadisticas'),
    path('administracion/reporte-semanal.csv', views.reporte_semanal_csv, name='reporte_semanal'),
]
