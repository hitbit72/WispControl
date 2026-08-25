from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render


from .forms import DispositivoForm, EnlaceForm, InterfazForm

from .models import Dispositivo, Enlace, Interfaz, TipoEquipo
from clientes.models import Cliente
from sector.models import Sector

from metricas.models import DeviceMetrics
from eventos.models import Evento
from eventos.services import registrar_evento

from core.rutas import http_ruta

MODULO = 'dispositivos'


@login_required
def lista_dispositivos(request):
    """ Listado global de dispositivos con búsqueda y filtros. """

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
    url_cancel = 'dispositivos:lista'

    if pk > 0:
        if 'sector' in url_anterior:
            sector = get_object_or_404(Sector, pk=pk)
            url_anterior = 'sector'
            url_cancel= 'sectores:detalle'
            #print('* SECTORES')
        elif 'cliente' in url_anterior:
            cliente = get_object_or_404(Cliente, pk=pk)
            url_anterior = 'cliente'
            url_cancel= 'clientes:detalle'
            #print('* CLIENTE')
        else:
            sector = ''
            cliente = ''
            dispositivo = ''
            url_cancel = 'dispositivos:lista'

    if request.method == 'POST':
        form = DispositivoForm(request.POST)
        url_anterior = request.POST.get('urlanterior')
        pk = int(request.POST.get('modelopk'))
        if form.is_valid():
            dispositivo = form.save()
            if url_anterior == 'sector':
                return redirect('sectores:detalle', pk=pk) if pk > 0 else redirect('sectores:lista')
            if url_anterior == 'cliente':
                return redirect('clientes:detalle', pk=pk) if pk > 0 else redirect('clientes:lista')
            return redirect('dispositivos:lista')
    else:
        form = DispositivoForm()
        if sector:
            form = DispositivoForm(initial={'sector': sector})
        if cliente:
            form = DispositivoForm(initial={'cliente': cliente})

    return render(request, 'dispositivo/form_dispositivo_solo.html', {
        'form': form,
        'sector': sector,
        'cliente': cliente,
        'modelo_pk': pk,
        'dispositivo': dispositivo,
        'url_anterior': url_anterior,
        'url_cancel': url_cancel,
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
    #print('detalle_dispositivo url_anterior: {url_anterior}')

    # cargar las metrcias del dispositivo
    metricas = DeviceMetrics.objects.filter(device=dispositivo).first()
   
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
    url_cancel= 'dispositivos:lista'

    # Obtiene la URL anterior, o asigna una ruta por defecto si no existe
    url_anterior = request.META.get('HTTP_REFERER', 'dispositivo')
    url_anterior = http_ruta(url_anterior, 'dispositivo')  # Cambia la ruta si es edicion

    if 'sector' in url_anterior:
        url_anterior = 'sectores:detalle'
        url_error = 'sectores:lista'
        modelo_pk = sector_pk
        #print('* SECTORES')
    elif 'cliente' in url_anterior:
        url_anterior = 'clientes:detalle'
        url_error = 'clientes:lista'
        modelo_pk = cliente_pk
        #print('* CLIENTE')
    else:
        url_anterior = 'dispositivos:detalle'
        url_error = 'dispositivos:lista'
        modelo_pk = pk
        #print('* DISPOSITIVO')

    if request.method == 'POST':
        form = DispositivoForm(request.POST, instance=dispositivo)
        if form.is_valid():
            dispositivo = form.save()
            url_anterior = form.cleaned_data.get('urlanterior')
            url_error = form.cleaned_data.get('urlerror')
            modelo_pk = form.cleaned_data.get('modelopk')
            return redirect(url_anterior, pk=modelo_pk) if sector_pk > 0 else redirect(url_error)
    else:
        form = DispositivoForm(instance=dispositivo)

    return render(request, 'dispositivo/form_dispositivo.html', {
        'form': form,
        'dispositivo': dispositivo,
        'modelo_pk': modelo_pk,
        'url_anterior': url_anterior,
        'url_error': url_error,
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



@login_required
def alternar_escaneo_dispositivo(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)

    if request.method == 'POST':
        metodo = request.POST.get('id_scanear')
        if metodo == '1':
            dispositivo.escanear = not dispositivo.escanear
            if not dispositivo.escanear:
                dispositivo.alarma = False    
        if metodo == '2':
            dispositivo.alarma = not dispositivo.alarma
            if dispositivo.alarma:
                dispositivo.escanear = True
        dispositivo.save()
    return redirect('dispositivos:detalle', pk=dispositivo.pk)


# --- Interfaces ----------------------------------------------------------------

@login_required
def nueva_interfaz(request, dispositivo_pk):
    dispositivo = get_object_or_404(Dispositivo, pk=dispositivo_pk)
    error_msg = ""

    if request.method == 'POST':
        form = InterfazForm(request.POST)
        if form.is_valid():
            interfaz = form.save(commit=False)
            interfaz.dispositivo = dispositivo
            interfaz.save()
            return redirect('dispositivos:detalle', pk=dispositivo.pk)
        else:
            # si el formlario no es válido.
            error_msg = "Por favor, corrige los errores en el formulario: " + form.errors.as_text()
    else:
        form = InterfazForm()

    return render(request, 'dispositivo/interfaz/form_interfaz.html', {
        'form': form, 'dispositivo': dispositivo, 'interfaz': None, 'error_msg': error_msg
    })



@login_required
def editar_interfaz(request, pk):
    interfaz = get_object_or_404(Interfaz, pk=pk)
    dispositivo_pk = interfaz.dispositivo_id

    if request.method == 'POST':
        form = InterfazForm(request.POST, instance=interfaz)
        if form.is_valid():
            form.save()
            return redirect('dispositivos:detalle', pk=dispositivo_pk)
    else:
        form = InterfazForm(instance=interfaz)

    return render(request, 'dispositivo/interfaz/form_interfaz.html', {
        'form': form, 'dispositivo': interfaz.dispositivo, 'interfaz': interfaz,
    })


@login_required
def eliminar_interfaz(request, pk):
    interfaz = get_object_or_404(Interfaz, pk=pk)
    dispositivo_pk = interfaz.dispositivo_id

    if request.method == 'POST':
        interfaz.delete()
        return redirect('dispositivos:detalle_dispositivo', pk=dispositivo_pk)

    return render(request, 'dispositivo/interfaz/confirmar_eliminar_interfaz.html', {'interfaz': interfaz})


# --- Enlaces ----------------------------------------------------------------

@login_required
def opciones_interfaces_dispositivo(request):
    """Fragmento HTMX con las opciones de interfaz_destino del dispositivo
    elegido en el formulario de enlaces."""
    destino_id = request.GET.get('dispositivo_destino', '').strip()
    if destino_id.isdigit():
        interfaces = Interfaz.objects.filter(
            dispositivo_id=destino_id
        ).order_by('nombre')
    else:
        interfaces = Interfaz.objects.none()
    return render(request, 'dispositivo/enlace/_opciones_interfaz.html', {'interfaces': interfaces})


@login_required
def nuevo_enlace(request, dispositivo_pk):
    """Crea un enlace cuyo origen es el dispositivo actual."""
    dispositivo = get_object_or_404(Dispositivo, pk=dispositivo_pk)

    if request.method == 'POST':
        form = EnlaceForm(request.POST, dispositivo_origen=dispositivo)
        if form.is_valid():
            enlace = form.save(commit=False)
            enlace.dispositivo_origen = dispositivo
            enlace.save()
            return redirect('dispositivos:detalle', pk=dispositivo.pk)
    else:
        form = EnlaceForm(dispositivo_origen=dispositivo)

    return render(request, 'dispositivo/enlace/form_enlace.html', {
        'form': form, 'dispositivo': dispositivo, 'enlace': None,
    })


@login_required
def editar_enlace(request, pk):
    enlace = get_object_or_404(Enlace, pk=pk)
    dispositivo_pk = enlace.dispositivo_origen_id
    error_msg = ""

    if request.method == 'POST':
        form = EnlaceForm(request.POST, instance=enlace, dispositivo_origen=enlace.dispositivo_origen)
        if form.is_valid():
            form.save()
            return redirect('dispositivos:detalle', pk=dispositivo_pk)
        else:
            # si el formlario no es válido.
            error_msg = "Por favor, corrige los errores en el formulario: " + form.errors.as_text()
    else:
        form = EnlaceForm(instance=enlace, dispositivo_origen=enlace.dispositivo_origen)

    return render(request, 'dispositivo/enlace/form_enlace.html', {
        'form': form, 'dispositivo': enlace.dispositivo_origen, 'enlace': enlace, 'error_msg': error_msg,
    })


@login_required
def eliminar_enlace(request, pk):
    enlace = get_object_or_404(Enlace, pk=pk)
    dispositivo_pk = enlace.dispositivo_origen_id

    if request.method == 'POST':
        registrar_evento(
	        MODULO,
	        f'Enlace {enlace.dispositivo_origen.nombre} eliminado',
	        f'Enlace eliminado #{enlace.dispositivo_origen_id} - {enlace.dispositivo_origen.nombre} → {enlace.dispositivo_destino.nombre}.',
	        nivel=Evento.Nivel.INFO,
        )
        enlace.delete()
        return redirect('dispositivos:detalle', pk=dispositivo_pk)

    return render(request, 'dispositivo/enlace/confirmar_eliminar_enlace.html', {'enlace': enlace})