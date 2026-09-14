from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from dispositivos.models import Dispositivo
from pingcontrol.services import ping_dispositivo as ejecutar_ping


@login_required
@require_POST
def ping_dispositivo(request, pk):
    """
    Ejecuta ping para un dispositivo y devuelve el resultado.
    """

    dispositivo = get_object_or_404(Dispositivo, pk=pk, ip_gestion__isnull=False)
    # Hacer ping
    exitoso, latencia, error_msg = ejecutar_ping(dispositivo)
    if error_msg:
        print(error_msg)

    return render(request, 'dispositivo/comun/_ping_result.html', {
        'exitoso': exitoso,
        'latencia': latencia,
        'error_msg': error_msg,
    })


