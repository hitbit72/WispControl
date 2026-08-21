from django import forms
from django.urls import reverse

from core.utils import BootstrapFormMixin
from .models import Sector


class SectorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Sector
        fields = [
            'nombre', 'poblacion', 'direccion', 'descripcion',
            'latitud', 'longitud', 'altitud',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

