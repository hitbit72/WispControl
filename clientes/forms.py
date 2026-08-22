from django import forms
from .models import Cliente, Contrato

from core.forms import BootstrapFormMixin


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Esto añade el atributo 'required' en el HTML y fuerza la validación en el servidor
        self.fields['telefono'].required = True

    class Meta:
        model = Cliente
        fields = [
            'nombre_completo', 'apodo', 'tipo_documento', 'numero_documento',
            'telefono', 'telefono_alternativo', 'email', 'poblacion', 'direccion',
            'latitud', 'longitud', 'activo', 'notas',
        ]
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 3}),
        }


class ContratoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            'nombre', 'plan', 'precio_mensual', 'estado', 'fecha_inicio', 'fecha_cancelacion',
            'conexion', 'identificador_mikrotik', 'pppoe_clave', 'ip_asignada', 'notas',
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'fecha_cancelacion': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'conexion': forms.Select(attrs={'x-on:change': 'conexion = $event.target.value'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
