#Configuracion de la administracion para las cuentas de clientes
from django.contrib import admin

from .models import Cuenta, MetodoPago, Pago


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'pide_referencia', 'orden')
    list_editable = ('activo', 'pide_referencia', 'orden')

#Pago en linea
class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    can_delete = False
    readonly_fields = ('metodo', 'monto', 'referencia',
                       'registrado_por', 'creado')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'estado', 'numero', 'total_cop',
                    'saldo_cop', 'creada')
    list_filter = ('estado',)
    inlines = [PagoInline]

    @admin.display(description='Total (COP)')
    def total_cop(self, obj):
        return f'${obj.total:,.0f}'

    @admin.display(description='Saldo (COP)')
    def saldo_cop(self, obj):
        return f'${obj.saldo:,.0f}'

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
