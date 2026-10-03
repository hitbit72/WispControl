from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from clientes.models import Cliente
from dispositivos.models import Dispositivo, Interfaz
from metricas.models import InterfaceMetricHistory
from eventos.models import Evento

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
    # Parámetros de tiempo
    periodo = request.GET.get('periodo', 'day')  # day, week, month, custom
    ahora = timezone.now()

    if periodo == 'hour':
        fecha_inicio = ahora - timedelta(hours=6)
        fecha_fin = ahora
    elif periodo == 'day':
        fecha_inicio = ahora - timedelta(days=1)
        fecha_fin = ahora
    elif periodo == 'week':
        fecha_inicio = ahora - timedelta(weeks=1)
        fecha_fin = ahora
    elif periodo == 'month':
        fecha_inicio = ahora - timedelta(days=30)
        fecha_fin = ahora
    else:
        fecha_inicio = ahora - timedelta(days=1)
        fecha_fin = ahora
        periodo = 'day'

    # Clientes
    clt = Cliente.objects.all()
    clientes = {
        'total': clt.count(),
        'activos': clt.filter(activo=True).count(),
        'inactivos': clt.filter(activo=False).count(),
        }
    clt = None

    # Dispositivos
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

    eventos = Evento.objects.filter(leido=False).order_by('nivel', '-fecha').all()

    return render(request, 'dashboard/inicio.html', {
        'usuario': request.user,
        'clientes': clientes,
        'dispositivos': dispositivos,
        'eventos': eventos,
        'mkt_dispositivo': mkt_dispositivo,
        'trafico_interfaces': json.dumps(trafico_interfaces),
        'periodo': periodo,
    })
