from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from sector.models import Sector
from .forms import PlanForm, RouterForm
from .models import Plan, Router

from eventos.models import Evento
from eventos.services import registrar_evento

MODULO = 'mikrotik'

def http_ruta(ruta):
    """
    Funcion para obtener la ruta de retorno a partir de la URL anterior. Se usa para
    evitar que al editar o crear un router/plan, la página de detalle redirija
    correctamente a la lista de routers en lugar de volver a la página de edición.
    """
    if any(palabra in ruta for palabra in ['editar', 'nuevo', 'eliminar']):
        return '/mikrotik/'
    
    return ruta # Devuelve la ruta original


@login_required
def lista_routers(request):
    """
    Listado de routers con búsqueda y filtro por sector. Si la petición
    viene de HTMX devuelve solo la tabla; si es una carga normal, la
    página completa con el formulario de filtros.
    """
    routers = Router.objects.select_related('sector')

    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        routers = routers.filter(
            Q(nombre__icontains=busqueda)
            | Q(ip__icontains=busqueda)
            | Q(modelo__icontains=busqueda)
        )

    sector_seleccionado = request.GET.get('sector', '').strip()
    if sector_seleccionado:
        routers = routers.filter(sector_id=sector_seleccionado)

    paginator = Paginator(routers, 25)
    pagina = paginator.get_page(request.GET.get('page'))

    contexto = {
        'pagina': pagina,
        'busqueda': busqueda,
        'sector_seleccionado': sector_seleccionado,
        'sectores': Sector.objects.order_by('nombre'),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mikrotik/_tabla.html', contexto)
    return render(request, 'mikrotik/lista.html', contexto)


@login_required
def detalle_router(request, pk):
    router = get_object_or_404(Router.objects.prefetch_related('planes'), pk=pk)
    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'mikrotik:lista')
    url_anterior = http_ruta(url_anterior)  # Cambia la ruta si es necesario

    return render(request, 'mikrotik/detalle.html', {'router': router, 'url_anterior': url_anterior})


@login_required
def form_router(request, pk=None):
    router = get_object_or_404(Router, pk=pk) if pk else None

    if request.method == 'POST':
        form = RouterForm(request.POST, instance=router)
        if form.is_valid():
            router = form.save()
            return redirect('mikrotik:detalle', pk=router.pk)
    else:
        form = RouterForm(instance=router)

    return render(request, 'mikrotik/form_router.html', {'form': form, 'router': router})


@login_required
def eliminar_router(request, pk):
    router = get_object_or_404(Router, pk=pk)
    if request.method == 'POST':
        router.delete()
        return redirect('mikrotik:lista')
    return render(request, 'mikrotik/confirmar_eliminar_router.html', {'router': router})


# PLANES -----------------------------------------------------------

@login_required
def nuevo_plan(request, router_pk):
    router = get_object_or_404(Router, pk=router_pk)

    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.router = router
            plan.save()
            registrar_evento(
                MODULO,
                'PLAN de internet registrado',
                f'Plan #{plan.pk}: {plan.nombre} - Down: {plan.velocidad_bajada} Mbps / Up: {plan.velocidad_subida} Mbps',
                nivel=Evento.Nivel.INFO,)
            return redirect('mikrotik:detalle', pk=router.pk)
    else:
        form = PlanForm()

    return render(request, 'mikrotik/form_plan.html', {
        'form': form, 'router': router, 'plan': None,
    })


@login_required
def editar_plan(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    router = plan.router

    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            registrar_evento(
                MODULO,
                'PLAN de internet modificado',
                f'Plan #{plan.pk}: {plan.nombre} - Down: {plan.velocidad_bajada} Mbps / Up: {plan.velocidad_subida} Mbps',
                nivel=Evento.Nivel.INFO,)
            return redirect('mikrotik:detalle', pk=router.pk)
    else:
        form = PlanForm(instance=plan)

    return render(request, 'mikrotik/form_plan.html', {
        'form': form, 'router': router, 'plan': plan,
    })



@login_required
def eliminar_plan(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    router_pk = plan.router_id
    #num_contratos = plan.contratos.count()

    if request.method == 'POST':
        registrar_evento(
            MODULO,
            'PLAN de internet eliminado',
            f'Plan #{plan.pk}: {plan.nombre}',
            nivel=Evento.Nivel.INFO,)
        plan.delete()
        return redirect('mikrotik:detalle', pk=router_pk)

    return render(request, 'mikrotik/confirmar_eliminar_plan.html', {'plan': plan})

