from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SectorForm
from .models import Sector

MODULO = 'sector'

@login_required
def lista_sectores(request):
    """Listado de sectores con búsqueda HTMX y paginación."""
    sectores = Sector.objects.all()

    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        sectores = sectores.filter(
            Q(nombre__icontains=busqueda) | Q(poblacion__icontains=busqueda)
        )

    paginator = Paginator(sectores, 25)
    pagina = paginator.get_page(request.GET.get('page'))

    contexto = {'pagina': pagina, 'busqueda': busqueda}

    if request.headers.get('HX-Request'):
        return render(request, 'sector/_tabla.html', contexto)
    return render(request, 'sector/lista.html', contexto)


@login_required
def detalle_sector(request, pk):
    sector = get_object_or_404(Sector, pk=pk)
    router_total = sector.routers_mikrotik.count()
    return render(request, 'sector/detalle_sector.html', {'sector': sector, 'routers': router_total})


@login_required
def form_sector(request, pk=None):
    sector = get_object_or_404(Sector, pk=pk) if pk else None

    if request.method == 'POST':
        form = SectorForm(request.POST, instance=sector)
        if form.is_valid():
            sector = form.save()
            return redirect('sectores:detalle_sector', pk=sector.pk)
    else:
        form = SectorForm(instance=sector)

    return render(request, 'sector/form_sector.html', {'form': form, 'sector': sector})


@login_required
def eliminar_sector(request, pk):
    sector = get_object_or_404(Sector, pk=pk)
    if request.method == 'POST':
        sector.delete()
        return redirect('sectores:lista')
    return render(request, 'sector/confirmar_eliminar_sector.html', {'sector': sector})
