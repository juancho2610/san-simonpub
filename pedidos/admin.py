# Register your models here for dashborad de pedidos.
from django.contrib import admin

from .models import DetallePedido, Pedido

#Clase del pedido del usuario
class DetallePedidoInline(admin.TabularInline):
	model = DetallePedido
	extra = 1
	autocomplete_fields = ['producto']

#Requiere acceso del administrador
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo', 'mesa', 'estado',
                    'total_cop', 'creado')
    list_filter = ('estado', 'tipo')
    readonly_fields = ('creado', 'actualizado')
    inlines = [DetallePedidoInline]

    @admin.display(description='Total (COP)')
    def total_cop(self, obj):
        return f'${obj.total:,.0f}'
