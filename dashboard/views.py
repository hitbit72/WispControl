from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def inicio(request):
    """
    Pantalla de inicio tras el login (Dashboard principal).
    """
    return render(request, 'dashboard/inicio.html', {
        'usuario': request.user,
    })