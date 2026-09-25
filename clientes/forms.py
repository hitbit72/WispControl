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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Evaluar si estamos editando un objeto existente (self.instance tiene PK)
        if self.instance and self.instance.pk:
            field = self.fields['identificador_mikrotik']
            # Deshabilitar el input en el HTML (no será editable)
            field.widget.attrs['disabled'] = 'disabled'
            # Quitar la obligación de envío en el POST
            field.required = False
            # ignora el POST para este campo para mantener el valor de la instancia
            field.disabled = True
        else:
            # Para nuevo registro añade el atributo 'required' en el HTML y fuerza la validación en el servidor
            self.fields['identificador_mikrotik'].required = True

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
