from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .context_processors import ROLES_PUEDEN_MARCAR
from .models import Evento


@login_required
def lista_eventos(request):
    """Listado de eventos. Los permisos para marcar como leído los valida
    cada vista de marcado; aquí solo se controla la sesión."""
    eventos = Evento.objects.all()

    filtro = request.GET.get('filtro', '').strip()
    if filtro == 'no_leidos':
        eventos = eventos.filter(leido=False)

    paginator = Paginator(eventos, 20)
    pagina = paginator.get_page(request.GET.get('page'))

    contexto = {
        'pagina': pagina,
        'filtro': filtro,
        'total_eventos': Evento.objects.count(),
        'eventos_pendientes': Evento.objects.filter(leido=False).count(),
        'puede_marcar_eventos': request.user.rol in ROLES_PUEDEN_MARCAR,
    }
    if request.headers.get('HX-Request'):
        return render(request, 'eventos/_tabla.html', contexto)
    return render(request, 'eventos/lista.html', contexto)


def _control_marcado(request):
    """Solo administrador y técnico pueden marcar eventos como leídos."""
    if request.user.rol not in ROLES_PUEDEN_MARCAR:
        return HttpResponseForbidden('No tienes permisos para marcar eventos.')
    return None


def _respuesta_marcado(request):
    if request.headers.get('HX-Request'):
        return _render_notificaciones(request)
    messages.success(request, 'Eventos marcados como leídos.')
    return redirect('eventos:lista')


@login_required
@require_POST
def marcar_leido(request, pk):
    control = _control_marcado(request)
    if control is not None:
        return control

    evento = get_object_or_404(Evento, pk=pk)
    if not evento.leido:
        evento.leido = True
        evento.user = request.user
        evento.save(update_fields=['leido', 'user'])
    return _respuesta_marcado(request)


@login_required
@require_POST
def marcar_todos_leidos(request):
    control = _control_marcado(request)
    if control is not None:
        return control

    Evento.objects.filter(leido=False).update(leido=True, user=request.user)
    return _respuesta_marcado(request)


def _render_notificaciones(request):
    contexto = {
        'eventos_notif': Evento.objects.filter(leido=False)[:6],
        'eventos_no_leidos': Evento.objects.filter(leido=False).count(),
        'puede_marcar_eventos': request.user.rol in ROLES_PUEDEN_MARCAR,
    }
    return render(request, 'eventos/_notificaciones.html', contexto)

