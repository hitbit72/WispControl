from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from clientes.models import Cliente
from dispositivos.models import Dispositivo, Interfaz
from metricas.models import InterfaceMetricHistory
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json

@login_required
def inicio(request):
    """
    Pantalla de inicio tras el login (Dashboard principal).
    """

    # Parametros para el gráfico
    ahora = timezone.now()
    fecha_inicio = ahora - timedelta(days=1)
    fecha_fin = ahora


    clt = Cliente.objects.all()
    clientes = {
        'total': clt.count(),
        'activos': clt.filter(activo=True).count(),
        'inactivos': clt.filter(activo=False).count(),
        }
    clt = None

    disp = Dispositivo.objects.all()
    # .first() devuelve un objeto Dispositivo (o None si no existe)
    mkt_dispositivo = Dispositivo.objects.filter(nombre__iexact='RB5009 Borde').first()
    dispositivos = {
        'total': disp.count(),
        'activos': disp.filter(estado='activo').count(),
        'inactivos': disp.filter(estado='inactivo').count(),
        'red': disp.filter(rol='main').count(),
        'st': disp.filter(rol='station').count(),
        'mkt': disp.filter(rol='mkt').count(),
        }
    disp = None

    # Tráfico de interfaces
    trafico_interfaces = {}
    if mkt_dispositivo:
        interfaces = mkt_dispositivo.interfaces.all()
        for interfaz in interfaces:
            trafico = InterfaceMetricHistory.objects.filter(
                interfaz=interfaz,
                timestamp__gte=fecha_inicio,
                timestamp__lte=fecha_fin
            ).order_by('timestamp')
            if trafico.exists():
                # Convert datetime to ISO string for JSON serialization
                trafico_interfaces[interfaz.nombre] = [
                    {'timestamp': t['timestamp'].isoformat(), 'rx': t['rx'], 'tx': t['tx']}
                    for t in trafico.values('timestamp', 'rx', 'tx')
                ]
    
    return render(request, 'dashboard/inicio.html', {
        'usuario': request.user,
        'clientes': clientes,
        'dispositivos': dispositivos,
        'mkt_dispositivo': mkt_dispositivo,
        'trafico_interfaces': json.dumps(trafico_interfaces),
    })
