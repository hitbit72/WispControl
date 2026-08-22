from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render


from .forms import DispositivoForm, EnlaceForm, InterfazForm

from .models import Dispositivo, Enlace, Interfaz, TipoEquipo
from clientes.models import Cliente
from sector.models import Sector
from eventos.models import Evento

#from metricas.models import DeviceMetrics
from eventos.services import registrar_evento
from core.rutas import http_ruta

MODULO = 'red'


@login_required
def lista_dispositivos(request):
    """Listado global de dispositivos (sin pasar por sectores), con búsqueda
    y filtros. Es una segunda vía de acceso: los dispositivos también se ven
    desde el detalle de su sector."""
    dispositivos = Dispositivo.objects.select_related('sector', 'cliente')
    
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        dispositivos = dispositivos.filter(
            Q(nombre__icontains=busqueda)
            | Q(modelo__icontains=busqueda)
            | Q(ip_gestion__icontains=busqueda)
            | Q(mac_address__icontains=busqueda)
        )

    tipo_seleccionado = request.GET.get('tipo', '').strip()
    if tipo_seleccionado:
        dispositivos = dispositivos.filter(tipo=tipo_seleccionado)

    estado_seleccionado = request.GET.get('estado', '').strip()
    if estado_seleccionado:
        dispositivos = dispositivos.filter(estado=estado_seleccionado)

    sector_seleccionado = request.GET.get('sector', '').strip()
    if sector_seleccionado:
        dispositivos = dispositivos.filter(sector_id=sector_seleccionado)

    dis_totales = dispositivos.count()
    dis_activos = dispositivos.filter(estado='activo').count()
    dis_inactivos = dispositivos.filter(estado='inactivo').count()
    dis_mantenimiento = dispositivos.filter(estado='mantenimiento').count()
    dis_instalacion = dispositivos.filter(estado='instalacion').count()
    dis_retirados = dispositivos.filter(estado='retirado').count()

    paginator = Paginator(dispositivos, 25)
    pagina = paginator.get_page(request.GET.get('page'))

    # lista de tipos de dispositivos
    tipos = (
        TipoEquipo.objects.exclude(clave='')
        .values_list('clave', 'nombre')
        .distinct()
        .order_by('nombre')
    )

    contexto = {
        'pagina': pagina,
        'busqueda': busqueda,
        'tipos': tipos,
        'tipo_seleccionado': tipo_seleccionado,
        'estado_seleccionado': estado_seleccionado,
        'tipos_dispositivo': Dispositivo.tipo,
        'tipos_estado': Dispositivo.Estado.choices,
        'sector_seleccionado': sector_seleccionado,
        'todos_sectores': Sector.objects.all().values_list('pk', 'nombre').order_by('nombre'),
        'totales': {
            'total': dis_totales,
            'activos': dis_activos,
            'inactivos': dis_inactivos,
            'mantenimiento': dis_mantenimiento,
            'instalacion': dis_instalacion,
            'retirados': dis_retirados,
        },
    }

    if request.headers.get('HX-Request'):
        return render(request, 'dispositivo/_tabla_dispositivos.html', contexto)
    return render(request, 'dispositivo/lista_dispositivos.html', contexto)


@login_required
def nuevo_dispositivo(request):

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivos/')

    if request.method == 'POST':
        form = DispositivoForm(request.POST)
        if form.is_valid():
            dispositivo = form.save()
            return redirect('red:lista_dispositivos')
    else:
        form = DispositivoForm()

    return render(request, 'dispositivo/form_dispositivo_solo.html', {
        'form': form,
        'sector': '',
        'cliente': '',
        'dispositivo': None,
        'url_anterior': url_anterior,
    })


@login_required
def nuevo_dispositivo_sector(request, sector_pk):
    sector = get_object_or_404(Sector, pk=sector_pk)

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'sectores/')

    if request.method == 'POST':
        form = DispositivoForm(request.POST)
        if form.is_valid():
            dispositivo = form.save()
            return redirect('sector:detalle_sector', pk=dispositivo.sector_id or sector.pk)
    else:
        form = DispositivoForm(initial={'sector': sector})

    return render(request, 'dispositivo/form_dispositivo_sector.html', {
        'form': form,
        'sector': sector,
        'dispositivo': None,
        'url_anterior': url_anterior,
    })



@login_required
def nuevo_dispositivo_cliente(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'clientes/')

    if request.method == 'POST':
        form = DispositivoForm(request.POST)
        if form.is_valid():
            dispositivo = form.save()
            return redirect('clientes:detalle', pk=cliente.pk)
    else:
        form = DispositivoForm(initial={'cliente': cliente})

    return render(request, 'dispositivo/form_dispositivo_cliente.html', {
        'form': form,
        'cliente': cliente,
        'dispositivo': None,
        'url_anterior': url_anterior,
    })


@login_required
def detalle_dispositivo(request, pk):
    dispositivo = get_object_or_404(
        Dispositivo.objects.prefetch_related('interfaces', 'enlaces_origen', 'enlaces_destino'),
        pk=pk,
    )

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivos/')
    url_anterior = http_ruta(url_anterior, 'dispositivos/')  # Cambia la ruta si es edicion
    print('detalle_dispositivo url_anterior: {url_anterior}')

    metricas = []
    # metricas = get_object_or_404(DeviceMetrics, device = pk)
    # procesar los datos tipo json antes de enviarlos a la platilla
    #if isinstance(metricas.puertos, str):
    #    metricas.puertos = json.loads(metricas.puertos)

    enlaces = sorted(
        (*dispositivo.enlaces_origen.all(), *dispositivo.enlaces_destino.all()),
        key=lambda e: e.pk,
    )
    return render(request, 'dispositivo/detalle_dispositivo.html', {
        'dispositivo': dispositivo,
        'enlaces': enlaces,
        'metricas': metricas,
        'url_anterior': url_anterior,
    })


@login_required
def editar_dispositivo(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)
    sector_pk = dispositivo.sector_id
    cliente_pk = dispositivo.cliente_id

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivos/')
    url_anterior = http_ruta(url_anterior, 'dispositivos/')  # Cambia la ruta si es edicion

    if request.method == 'POST':
        form = DispositivoForm(request.POST, instance=dispositivo)
        url_anterior = request.POST.get('urlanterior')
        if form.is_valid():
            dispositivo = form.save()
            if 'sectores' in url_anterior:
                return redirect('sectores:detalle_sector', pk=dispositivo.sector_id or sector_pk)
            if 'clientes' in url_anterior:
                return redirect('clientes:detalle', pk=dispositivo.cliente_id or cliente_pk)
            return redirect('dispositivos:detalle_dispositivo', pk=pk)
    else:
        form = DispositivoForm(instance=dispositivo)

    return render(request, 'dispositivo/form_dispositivo.html', {
        'form': form,
        'sector': dispositivo.sector,
        'dispositivo': dispositivo,
        'url_anterior': url_anterior,
    })


@login_required
def editar_dispositivo_cliente(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)
    cliente_pk = dispositivo.cliente_id

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivos/')
    url_anterior = http_ruta(url_anterior, 'clientes/')  # Cambia la ruta si es edicion

    if request.method == 'POST':
        form = DispositivoForm(request.POST, instance=dispositivo)
        url_anterior = request.POST.get('urlanterior')
        if form.is_valid():
            dispositivo = form.save()
            return redirect('clientes:detalle', pk=dispositivo.cliente_id or cliente_pk)
    else:
        form = DispositivoForm(instance=dispositivo)

    return render(request, 'dispositivo/form_dispositivo.html', {
        'form': form,
        'cliente': dispositivo.cliente,
        'dispositivo': dispositivo,
        'url_anterior': url_anterior,
    })


@login_required
def editar_dispositivo_sector(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)
    sector_pk = dispositivo.sector_id

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivos/')
    url_anterior = http_ruta(url_anterior, 'clientes/')  # Cambia la ruta si es edicion

    if request.method == 'POST':
        form = DispositivoForm(request.POST, instance=dispositivo)
        url_anterior = request.POST.get('urlanterior')
        if form.is_valid():
            dispositivo = form.save()
            return redirect('sectores:detalle_sector', pk=dispositivo.sector_id or sector_pk)
    else:
        form = DispositivoForm(instance=dispositivo)

    return render(request, 'dispositivo/form_dispositivo.html', {
        'form': form,
        'sector': dispositivo.sector,
        'dispositivo': dispositivo,
        'url_anterior': url_anterior,
    })


@login_required
def eliminar_dispositivo(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)

    if request.method == 'POST':
        registrar_evento(
	        MODULO,
	        f'Dipositivo {dispositivo.nombre} eliminado',
	        f'Dispositivo #{dispositivo.pk} - {dispositivo.marca} {dispositivo.ip_gestion}.',
	        nivel=Evento.Nivel.INFO,
        )
        dispositivo.delete()
        return redirect('dispositivos:lista')

    return render(request, 'dispositivo/confirmar_eliminar_dispositivo.html', {'dispositivo': dispositivo})


# --- Enlaces ----------------------------------------------------------------
