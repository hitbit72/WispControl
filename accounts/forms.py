from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from core.utils import BootstrapFormMixin
from .models import Usuario


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """Login con estilos Bootstrap. Se usa como `authentication_form`
    en el LoginView."""


class FormPasswordCambio(BootstrapFormMixin, PasswordChangeForm):
    """Cambio de contraseña del usuario autenticado, con estilos Bootstrap."""


class PerfilForm(BootstrapFormMixin, forms.ModelForm):
    """Datos editables del propio usuario autenticado. El 'username' y el
    'rol' no se tocan desde aquí (los gestiona el administrador)."""

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'activo_en_campo']