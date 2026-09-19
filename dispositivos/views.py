from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DispositivoForm, EnlaceForm, InterfazForm

from .models import Dispositivo, Enlace, Interfaz, TipoEquipo, dispositivos_ap
from clientes.models import Cliente
from sector.models import Sector

from metricas.models import DeviceMetrics, Alarma
from eventos.models import Evento
from eventos.services import registrar_evento

#from core.rutas import http_ruta

MODULO = 'dispositivos'

@login_required
def buscar_dispositivo(request, query):
    # 'query' contendrá la cadena enviada en la URL (ej: "192.168.25.50" "equipo1")
    dispositivo = Dispositivo.objects.filter(
        Q(nombre__icontains=query) 
        | Q(nombre_host__icontains=query)
        | Q(ip_gestion__icontains=query)
        | Q(ip_publica__icontains=query)
    ).first()

    if not dispositivo:
        raise Http404("No se encontró ningún dispositivo.")
    
    return detalle_dispositivo(request, dispositivo.pk)



@login_required
def lista_dispositivos(request):
    """ Listado global de dispositivos con búsqueda y filtros. """

    dispositivos = Dispositivo.objects.select_related(
        'sector', 'cliente'
        ).prefetch_related(
            'metricas',
            Prefetch(
				'alarmas',
				queryset=Alarma.objects.filter(estado='activa', tipo='snmp')
			)
        ).all()
    
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        dispositivos = dispositivos.filter(
            Q(nombre__icontains=busqueda)
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

    sector = ''
    cliente = ''
    dispositivo = ''
    error_msg = ''

    # Capturamos la URL de redirección (si viene en el GET o en el POST)
    url_anterior = request.POST.get('next') or request.GET.get('next')
                                                               
    if pk > 0:
        if 'sectores' in url_anterior:
            #sector = get_object_or_404(Sector, pk=pk)
            sector = Sector.objects.filter(pk=pk).first()
        elif 'clientes' in url_anterior:
            cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        form = DispositivoForm(request.POST)
        if form.is_valid():
            dispositivo = form.save()
            if url_anterior:
                return redirect(url_anterior)
            return redirect('dispositivos:lista')
        else:
            # si el formlario no es válido.
            error_msg = "Por favor, corrige los errores del formulario: " + form.errors.as_text()
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
        'error_msg': error_msg,
    })


@login_required
def detalle_dispositivo(request, pk):
    dispositivo = get_object_or_404(
        Dispositivo.objects.prefetch_related(
            'interfaces', 
            'metricas',
            Prefetch(
				'alarmas',
				queryset=Alarma.objects.filter(estado='activa', tipo='snmp')
			)
        ),
        pk=pk,
    )

    # Capturamos la URL de redirección (si viene en el GET o en el POST)
    url_anterior = request.POST.get('next') or request.GET.get('next')

    # Obtener las métricas asociada al dispositivo
    metricas = dispositivo.metricas.first()

    # si es main, buscamos las estaciones
    estaciones = ''
    devices = []
    if metricas:
        if dispositivo.rol == 'main':
            estaciones = (
                DeviceMetrics.objects
                .select_related('device')
                .filter(ssid=metricas.ssid,)
                .exclude(device=dispositivo)
            )

        
        # ---- a partir de aqui, es para crear una lista combinada de estaciones registradas y estaciones detectadas por el AP
        
        # Primero las estaciones registradas
        for metrica in estaciones:
            cl_pk = 0
            cl_name = metrica.device.nombre
            if metrica.device.cliente:
                cl_pk = metrica.device.cliente.pk
                cl_name = metrica.device.cliente.nombre_completo
            devices.append({
                'registrado': True,
                'estado': metrica.device.estado,
                'ip_gestion': metrica.device.ip_gestion,
                'device_pk': metrica.device.pk,
                'cliente': cl_name,
                'cliente_pk': cl_pk,
                'nombre_host': metrica.device.nombre_host,
                'signal': metrica.signal,
                'noise': metrica.noise,
                'ccq': metrica.ccq,
                'distancia': metrica.distancia,
                'tx': metrica.tx,
                'rx': metrica.rx,
            })

        # IPs que ya tienes
        ips_estaciones = {
            metrica.device.ip_gestion
            for metrica in estaciones
        }

        # Después añadimos los dispositivos que no están en estaciones registradas
        for device in metricas.estaciones:
            if device['ip'] not in ips_estaciones:
                devices.append({
                    'registrado': False,
                    'estado': 'activo',
                    'ip_gestion': device['ip'],
                    'device_pk': 0,
                    'cliente': '—',
                    'cliente_pk': 0,
                    'nombre_host': device['host'],
                    'signal': device['signal'],
                    'noise': device['noise'],
                    'ccq': device['ccq'],
                    'distancia': device['distancia'],
                    'tx': device['tx_rate'],
                    'rx': device['rx_rate'],
                })
    
        # ----------- FIN COMBINACION DE LISTAS ---------------------

    # contar el número de alarmas que tiene
    hay_alarmas = dispositivo.alarmas.count()

    return render(request, 'dispositivo/detalle_dispositivo.html', {
        'dispositivo': dispositivo,
        'metricas': metricas,
        'estaciones': devices,
        'url_anterior': url_anterior,
        'hay_alarmas': hay_alarmas,
        'dispositivos_ap': dispositivos_ap,
    })


@login_required
def detalle_dispositivo2(request, pk):
    dispositivo = get_object_or_404(
        Dispositivo.objects.prefetch_related(
            'interfaces', 
            'enlaces_origen', 
            'enlaces_destino', 
            'metricas'),
        pk=pk,
    )

    # Capturamos la URL de redirección (si viene en el GET o en el POST)
    url_anterior = request.POST.get('next') or request.GET.get('next')
    
    # cargar las metrcias del dispositivo
    #metricas = DeviceMetrics.objects.filter(device=dispositivo).first()
    metricas = dispositivo.metricas.first()  # Obtener la primera métrica asociada al dispositivo

    enlaces = sorted(
        (*dispositivo.enlaces_origen.all(), *dispositivo.enlaces_destino.all()),
        key=lambda e: e.pk,
    )

    return render(request, 'dispositivo/detalle_dispositivo2.html', {
        'dispositivo': dispositivo,
        'enlaces': enlaces,
        'metricas': metricas,
        'url_anterior': url_anterior,
        'dispositivos_ap': dispositivos_ap,
    })

@login_required
def editar_dispositivo(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)

    # Capturamos la URL de redirección (si viene en el GET o en el POST)
    url_anterior = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        form = DispositivoForm(request.POST, instance=dispositivo)
        if form.is_valid():
            dispositivo = form.save()
            if url_anterior:
                return redirect(url_anterior)
            return redirect('dispositivos:lista')
    else:
        form = DispositivoForm(instance=dispositivo)

    return render(request, 'dispositivo/form_dispositivo.html', {
        'form': form,
        'dispositivo': dispositivo,
        'url_anterior': url_anterior,
    })


@login_required
def eliminar_dispositivo(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)

    # Capturamos la URL de redirección (si viene en el GET o en el POST)
    url_anterior = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        registrar_evento(
	        MODULO,
	        f'Dipositivo {dispositivo.nombre} eliminado',
	        f'Dispositivo #{dispositivo.pk} - {dispositivo.marca.nombre} {dispositivo.marca.modelo} {dispositivo.ip_gestion}.',
	        nivel=Evento.Nivel.INFO,
        )
        dispositivo.delete()
        if url_anterior:
            return redirect(url_anterior)
        return redirect('dispositivos:lista')
    
    return render(request, 'dispositivo/confirmar_eliminar_dispositivo.html', {
        'dispositivo': dispositivo,
        'url_anterior': url_anterior,
        })



@login_required
def alternar_escaneo_dispositivo(request, pk):

    dispositivo = get_object_or_404(Dispositivo, pk=pk)

    if request.method == 'POST':
        dispositivo.escanear = 'escanear' in request.POST
        dispositivo.alarma = 'alarma' in request.POST
        dispositivo.alarma_puerto = 'alarma_puerto' in request.POST
        dispositivo.ping = 'ping' in request.POST
        dispositivo.alarma_ping = 'alarma_ping' in request.POST
        dispositivo.save()
    
    return render(request, 'dispositivo/comun/_opt_escanear.html', {
        'dispositivo': dispositivo,
        })



# Vista obsoleta, usa botones para cambio de estado. Ahora usamos un formulario
@login_required
def alternar_escaneo_dispositivo_noUsada(request, pk):
    dispositivo = get_object_or_404(Dispositivo, pk=pk)

    if request.method == 'POST':
        metodo = request.POST.get('id_scanear')

        if metodo == '1':
            dispositivo.escanear = not dispositivo.escanear
        if metodo == '2':
            dispositivo.alarma = not dispositivo.alarma
        if metodo == '3':
            dispositivo.alarma_puerto = not dispositivo.alarma_puerto

        if metodo == '4':
            dispositivo.ping = not dispositivo.ping
        if metodo == '5':
            dispositivo.alarma_ping = not dispositivo.alarma_ping

        # Si no hay escaneo, se desactivan las alarmas
        if not dispositivo.escanear:
            #dispositivo.alarma = False    
            dispositivo.alarma_puerto = False

        if not dispositivo.alarma:
            dispositivo.alarma_puerto = False

        if not dispositivo.ping:
            dispositivo.alarma_ping = False

        dispositivo.save()

    return render(request, 'dispositivo/comun/_bt_scanear.html', {
        'dispositivo': dispositivo,
        })


# --- Interfaces ----------------------------------------------------------------
# 1bsp = 0,000001 mbps

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
            error_msg = "Por favor, corrige los errores del formulario: " + form.errors.as_text()
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
        return redirect('dispositivos:detalle', pk=dispositivo_pk)

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
            error_msg = "Por favor, corrige los errores del formulario: " + form.errors.as_text()
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