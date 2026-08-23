from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render


from .forms import DispositivoForm, EnlaceForm, InterfazForm

from .models import Dispositivo, Enlace, Interfaz, TipoEquipo
from clientes.models import Cliente
from sector.models import Sector

#from metricas.models import DeviceMetrics
from eventos.models import Evento
from eventos.services import registrar_evento

from core.rutas import http_ruta

MODULO = 'dispositivos'


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

    contexto = {
        'pagina': pagina,
        'busqueda': busqueda,
        'tipo_seleccionado': tipo_seleccionado,
        'todos_tipos': TipoEquipo.objects.all().values_list('pk', 'nombre').order_by('nombre'),
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
def nuevo_dispositivo(request, pk=0):

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivos/')

    sector = ''
    cliente = ''
    dispositivo = ''
    if pk > 0:
        if 'sector' in url_anterior:
            sector = get_object_or_404(Sector, pk=pk)
            url_anterior = 'sector'
            #print('* SECTORES')
        if 'cliente' in url_anterior:
            cliente = get_object_or_404(Cliente, pk=pk)
            url_anterior = 'cliente'
            #print('* CLIENTE')

    if request.method == 'POST':
        form = DispositivoForm(request.POST)
        url_anterior = request.POST.get('urlanterior')
        pk = request.POST.get('modelopk')
        if form.is_valid():
            dispositivo = form.save()
            if url_anterior == 'sector':
                if pk > 0:
                    return redirect('sectores:detalle', pk=pk)
                else:
                    return redirect('sectores:lista')
            if url_anterior == 'cliente':
                if pk > 0:
                    return redirect('clientes:detalle', pk=pk)
                else:
                    return redirect('clientes:lista')
            return redirect('dispositivos:lista')
    else:
        if not sector:
            if cliente:
                form = DispositivoForm(initial={'cliente': cliente})
            else:
                form = DispositivoForm()
        else:
            form = DispositivoForm(initial={'sector': sector})


    return render(request, 'dispositivo/form_dispositivo_solo.html', {
        'form': form,
        'sector': sector,
        'cliente': cliente,
        'modelo_pk': pk,
        'dispositivo': dispositivo,
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
    modelo_pk = 0

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivo')
    url_anterior = http_ruta(url_anterior, 'dispositivo')  # Cambia la ruta si es edicion

    if 'dispositivo' in url_anterior:
        url_anterior = 'dispositivo'
        #print('* DISPOSITIVO')
    if 'sector' in url_anterior:
        url_anterior = 'sector'
        modelo_pk = sector_pk
        #print('* SECTORES')
    if 'cliente' in url_anterior:
        url_anterior = 'cliente'
        modelo_pk = cliente_pk
        #print('* CLIENTE')

    if request.method == 'POST':
        form = DispositivoForm(request.POST, instance=dispositivo)
        url_anterior = request.POST.get('urlanterior')
        if form.is_valid():
            dispositivo = form.save()
            if 'sector' in url_anterior:
                if sector_pk > 0:
                    return redirect('sectores:detalle', pk=dispositivo.sector_id or sector_pk)
                else:
                    return redirect('sectores:lista')
            if 'cliente' in url_anterior:
                if cliente_pk > 0:
                    return redirect('clientes:detalle', pk=dispositivo.cliente_id or cliente_pk)
                else:
                    return redirect('clientes:lista')
            return redirect('dispositivos:detalle_dispositivo', pk=pk)
    else:
        form = DispositivoForm(instance=dispositivo)

    return render(request, 'dispositivo/form_dispositivo.html', {
        'form': form,
        'dispositivo': dispositivo,
        'modelo_pk': modelo_pk,
        'url_anterior': url_anterior,
    })


@login_required
def eliminar_dispositivo(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)
    sector_pk = dispositivo.sector_id
    cliente_pk = dispositivo.cliente_id
    modelo_pk = 0

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivo')
    url_anterior = http_ruta(url_anterior, 'dispositivo')  # Cambia la ruta si es edicion

    if 'dispositivo' in url_anterior:
        url_anterior = 'dispositivo'
        print('* DISPOSITIVO')
    if 'sector' in url_anterior:
        url_anterior = 'sector'
        modelo_pk = sector_pk
        print('* SECTORES')
    if 'cliente' in url_anterior:
        url_anterior = 'cliente'
        modelo_pk = cliente_pk
        print('* CLIENTE')

    if request.method == 'POST':
        registrar_evento(
	        MODULO,
	        f'Dipositivo {dispositivo.nombre} eliminado',
	        f'Dispositivo #{dispositivo.pk} - {dispositivo.marca.nombre} {dispositivo.marca.modelo} {dispositivo.ip_gestion}.',
	        nivel=Evento.Nivel.INFO,
        )
        url_anterior = request.POST.get('urlanterior')
        pk = request.POST.get('modelopk')
        dispositivo.delete()
        if 'sector' in url_anterior:
            if pk > 0:
                return redirect('sectores:detalle', pk=pk)
            else:
                return redirect('sectores:lista')
        if 'cliente' in url_anterior:
            if pk > 0:
                return redirect('clientes:detalle', pk=pk)
            else:
                return redirect('clientes:lista')
        return redirect('dispositivos:lista')

    return render(request, 'dispositivo/confirmar_eliminar_dispositivo.html', {
        'dispositivo': dispositivo,
        'url_anterior': url_anterior,
        'modelo_pk': modelo_pk,
        })


# --- Enlaces ----------------------------------------------------------------
