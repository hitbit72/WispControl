from django import forms

from core.forms import BootstrapFormMixin
from .models import Plan, Router


class RouterForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Router
        fields = [
            'nombre', 'modelo', 'usuario', 'clave', 'ip', 'puerto', 'sector',
            'active_list', 'ppp_disable', 'latitud', 'longitud', 'notas',
        ]
        widgets = {
            'clave': forms.PasswordInput(render_value=True),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }


class PlanForm(BootstrapFormMixin, forms.ModelForm):
    """'router' no se edita desde el formulario: se fija desde la vista
    al crear un plan bajo un router concreto (igual que 'cliente' en
    ContratoForm)."""

    class Meta:
        model = Plan
        fields = [
            'nombre', 'velocidad_bajada', 'velocidad_subida', 'parent', 'before',
            'addr_list', 'limit_down', 'limit_up', 'priority_down', 'priority_up',
        ]