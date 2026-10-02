from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from clientes.models import Cliente
from dispositivos.models import Dispositivo

@login_required
def inicio(request):
    """
    Pantalla de inicio tras el login (Dashboard principal).
    """

    clt = Cliente.objects.all()
    clientes = {
        'total': clt.count(),
        'activos': clt.filter(activo=True).count(),
        'inactivos': clt.filter(activo=False).count(),
        }
    clt = None

    disp = Dispositivo.objects.all()
    dispositivos = {
        'total': disp.count(),
        'activos': disp.filter(estado='activo').count(),
        'inactivos': disp.filter(estado='inactivo').count(),
        'ap': disp.filter(rol='main').count(),
        'st': disp.filter(rol='station').count(),
        'mkt': disp.filter(rol='mkt').count(),
        }
    disp = None

    return render(request, 'dashboard/inicio.html', {
        'usuario': request.user,
        'clientes': clientes,
        'dispositivos': dispositivos,
    })