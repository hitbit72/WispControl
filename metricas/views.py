from io import StringIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from dispositivos.models import Dispositivo
from metricas.management.commands.monitorizar import Command as MonitorizarCommand


@login_required
@require_POST
def actualizar_metricas_snmp(request, pk):
    """
    Ejecuta la consulta SNMP para un dispositivo y devuelve el partial
    con las métricas actualizadas.
    """
    dispositivo = get_object_or_404(Dispositivo, pk=pk, ip_gestion__isnull=False)

    # Ejecutar la lógica de monitorizado directamente (sin subprocess)
    cmd = MonitorizarCommand()
    cmd.stdout = StringIO()
    try:
        cmd._procesar(dispositivo)
    except Exception:
        print('Error actualizar snmp')
        # En caso de error, igual intentamos devolver la métrica actual
        pass

    metricas = dispositivo.metricas.first()

    return render(request, 'dispositivo/_metricas_partial.html', {
        'metricas': metricas,
        'dispositivo': dispositivo,
    })