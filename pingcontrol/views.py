from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from dispositivos.models import Dispositivo
from pingcontrol.services import ping_detalles


@login_required
@require_POST
def ping_dispositivo(request, pk):
    """
    Ejecuta ping para un dispositivo y devuelve el resultado.
    """

    dispositivo = get_object_or_404(Dispositivo, pk=pk, ip_gestion__isnull=False)
    # Hacer ping
    exitoso, latencia, resultado, error_msg = ping_detalles(dispositivo)
    if error_msg:
        print(error_msg)
    
    return render(request, 'dispositivo/comun/_ping_result.html', {
        'exitoso': exitoso,
        'latencia': latencia,
        'resultado': str(resultado),
        'error_msg': error_msg,
    })


