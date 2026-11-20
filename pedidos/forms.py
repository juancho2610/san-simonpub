#Formulario para los pedidos
from django import forms
from django.conf import settings

from .models import Pedido

#Clase Pedidos en formulario
class PedidoForm(forms.ModelForm):
    mesa = forms.IntegerField(
        required=False, min_value=1, max_value=settings.MESAS_TOTAL,
        label='Número de mesa')
    guardar_direccion = forms.BooleanField(
        required=False, label='Guardar como mi dirección')

    class Meta:
        model = Pedido
        fields = ('tipo', 'mesa', 'direccion_entrega',
                  'telefono_contacto', 'notas')
        labels = {
            'direccion_entrega': 'Dirección de entrega',
            'telefono_contacto': 'Teléfono de contacto',
        }
        widgets = {'notas': forms.Textarea(attrs={'rows': 2})}

    def clean(self):
        datos = super().clean()
        tipo = datos.get('tipo')
        # Se descartan los datos que no aplican al tipo de pedido elegido.
        if tipo != Pedido.Tipo.EN_MESA:
            datos['mesa'] = None
        if tipo != Pedido.Tipo.DOMICILIO:
            datos['direccion_entrega'] = ''
            datos['guardar_direccion'] = False
        if tipo == Pedido.Tipo.EN_MESA:
            datos['telefono_contacto'] = ''
        return datos
