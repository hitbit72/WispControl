from django import forms
from django.urls import reverse


from core.forms import BootstrapFormMixin
from .models import Dispositivo, Enlace, Interfaz


def _etiqueta_dispositivo(obj):
    """Etiqueta del selector de dispositivo destino: 'nombre (tipo · IP · sector)'."""
    ip = obj.ip_gestion or 'sin IP'
    sector = obj.sector.nombre if obj.sector_id else 'Sin sector'
    return f'{obj.nombre} ({obj.tipo.nombre} · {ip} · {sector})'


def _etiqueta_interfaz(obj):
    """Etiqueta de interfaz: 'nombre · IP', coherente con el fragmento HTMX."""
    ip = obj.ip_address or 'sin IP'
    return f'{obj.nombre} · {ip}'


class JSONTextoOpcional(forms.JSONField):
    """
    Campo JSON tolerante: si el texto introducido es JSON válido se guarda
    como dict/list; si no, se guarda el texto tal cual (como string) en vez
    de rechazar el formulario. Así un usuario no pierde el formulario por
    escribir un formato suelto (p.ej. 'modelo: lhg').
    """

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, (list, dict, int, float)):
            return value
        if isinstance(value, str) and not value.strip():
            return None
        try:
            return super().to_python(value)
        except forms.ValidationError:
            return value.strip()

class DispositivoForm(BootstrapFormMixin, forms.ModelForm):
    """'sector' se puede seleccionar en el formulario; al crear un dispositivo
    bajo un sector concreto la vista lo preselecciona como valor inicial."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Esto añade el atributo 'required' en el HTML y fuerza la validación en el servidor
        self.fields['ip_gestion'].required = True
        self.fields['fecha_instalacion'].required = True
        self.fields['mac_address'].required = True

    atributos_extra = JSONTextoOpcional(
        required=False,
        label='Atributos del dispositivo',
        help_text='Datos específicos de la marca/modelo. Puedes escribir texto suelto o un objeto JSON válido (p.ej. {"banda": 5}).',
        widget=forms.Textarea(attrs={'rows': 5}),
    )

    class Meta:
        model = Dispositivo
        fields = [
            'nombre', 'nombre_host', 'rol', 'tipo', 'marca', 'onu_ref', 'sector', 'cliente', 'frequency',
            'ip_gestion', 'ip_publica', 'mac_address', 'firmware_version', 'snmp_community', 'escanear', 'alarma', 
            'alarma_puerto', 'ping', 'alarma_ping', 'estado', 'fecha_instalacion', 'latitud', 'longitud', 'atributos_extra', 'notas',
        ]
        widgets = {
            'fecha_instalacion': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
            'escanear': forms.CheckboxInput(),
            'alarma': forms.CheckboxInput(),
            'alarma_puerto': forms.CheckboxInput(),
            'ping': forms.CheckboxInput(),
            'alarma_ping': forms.CheckboxInput(),
        }


class InterfazForm(BootstrapFormMixin, forms.ModelForm):
    """'dispositivo' se fija desde la vista."""

    class Meta:
        model = Interfaz
        fields = [
            'nombre', 'tipo', 'estado', 'ip_address', 'mac_address', 'velocidad_mbps',
        ]


class EnlaceForm(BootstrapFormMixin, forms.ModelForm):
    """'dispositivo_origen' se fija desde la vista; la lista de interfaces
    origen se restringe a las del dispositivo origen. El destino se etiqueta
    con 'nombre (tipo · IP · sector)' y sus interfaces se cargan dinámicamente
    vía HTMX al cambiar el dispositivo destino."""

    def __init__(self, *args, dispositivo_origen=None, **kwargs):
        super().__init__(*args, **kwargs)
        if dispositivo_origen is not None:
            self.fields['interfaz_origen'].queryset = dispositivo_origen.interfaces.all()
            self.fields['dispositivo_destino'].queryset = Dispositivo.objects.exclude(
                pk=dispositivo_origen.pk
            ).select_related('sector')

        destino = self.fields['dispositivo_destino']
        destino.label_from_instance = _etiqueta_dispositivo
        destino.widget.attrs.update({
            'hx-get': reverse('dispositivos:opciones_interfaces_dispositivo'),
            'hx-trigger': 'change',
            'hx-target': '#id_interfaz_destino',
            'hx-swap': 'innerHTML',
            'hx-include': '#id_dispositivo_destino',
        })
        # Esto añade el atributo 'required' en el HTML y además fuerza la validación en el servidor
        self.fields['interfaz_origen'].required = True
        self.fields['interfaz_destino'].required = True

        for campo in ('interfaz_origen', 'interfaz_destino'):
            self.fields[campo].label_from_instance = _etiqueta_interfaz

        if self.is_bound:
            destino_id = self.data.get('dispositivo_destino')
            if destino_id:
                self.fields['interfaz_destino'].queryset = Interfaz.objects.filter(
                    dispositivo_id=destino_id
                )
        elif self.instance and self.instance.dispositivo_destino_id:
            self.fields['interfaz_destino'].queryset = self.instance.dispositivo_destino.interfaces.all()

    class Meta:
        model = Enlace
        fields = [
            'dispositivo_destino', 'interfaz_origen', 'interfaz_destino',
            'tipo', 'ancho_banda_mbps', 'distancia_km', 'frecuencia_ghz', 'notas',
        ]
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 3}),
        }