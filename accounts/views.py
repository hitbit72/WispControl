from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import FormPasswordCambio, PerfilForm, LoginForm


@login_required
def inicio(request):
    """
    Pantalla de inicio tras el login.
    En la fase de núcleo solo confirma que el acceso y los roles funcionan.
    El dashboard real (métricas, alarmas, mapa) llega en la fase de monitorización.
    """
    return render(request, 'accounts/inicio.html', {
        'usuario': request.user,
    })


@login_required
def perfil(request):
    """Ver y editar los datos personales del usuario autenticado."""
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('accounts:perfil')
    else:
        form = PerfilForm(instance=request.user)

    return render(request, 'accounts/perfil.html', {'form': form})


class CambiarContrasenaView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/cambiar_contrasena.html'
    form_class = FormPasswordCambio
    success_url = reverse_lazy('accounts:cambiar_contrasena_ok')


class CambiarContrasenaOkView(PasswordChangeDoneView):
    template_name = 'accounts/contrasena_cambiada.html'
