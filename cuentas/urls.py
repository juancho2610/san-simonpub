from django.urls import path

from . import views

urlpatterns = [
    path('personal/cuentas/', views.lista, name='cuentas_lista'),
    path('personal/cuentas/<int:pk>/', views.detalle, name='cuenta_detalle'),
    path('personal/cuentas/<int:pk>/cobrar/', views.cobrar, name='cuenta_cobrar'),
    path('personal/cuentas/<int:pk>/pendiente/', views.pendiente, name='cuenta_pendiente'),
]
