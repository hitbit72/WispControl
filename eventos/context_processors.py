from .models import Evento

ROLES_PUEDEN_MARCAR = ('administrador', 'tecnico')


def notificaciones(request):
    """Datos para las Notificaciones de base.html: los 6 eventos sin leer
    más importantes (primero por nivel 0→6 y después por fecha desc)."""
    if not request.user.is_authenticated:
        return {
            'eventos_notif': Evento.objects.none(),
            'eventos_no_leidos': 0,
            'puede_marcar_eventos': False,
        }

    sin_leer = Evento.objects.filter(leido=False)
    return {
        'eventos_notif': sin_leer[:6],
        'eventos_no_leidos': sin_leer.count(),
        'puede_marcar_eventos': request.user.rol in ROLES_PUEDEN_MARCAR,
    }