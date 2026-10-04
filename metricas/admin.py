from django.contrib import admin

from .models import Alarma, DeviceMetrics, DeviceMetricHistory, OIDmetric, DeviceLatencyHistory, InterfaceMetricHistory


@admin.register(DeviceMetrics)
class DeviceMetricsAdmin(admin.ModelAdmin):
    list_display = ('device', 'status', 'cpu', 'ram', 'frequency', 'clients')
    list_filter = ('status', 'device__tipo', 'device__marca')
    date_hierarchy = 'timestamp'
    search_fields = ('device__nombre',)
    readonly_fields = ('device', 'timestamp', 'timescan')
    list_select_related = ('device',)


@admin.register(DeviceMetricHistory)
class DeviceHistoryAdmin(admin.ModelAdmin):
    list_display = ('device', 'cpu', 'ram', 'timestamp')
    date_hierarchy = 'timestamp'
    search_fields = ('device__nombre',)
    readonly_fields = ('device', 'timestamp')

@admin.register(Alarma)
class AlarmaAdmin(admin.ModelAdmin):
    list_display = ('device', 'titulo', 'tipo', 'nivel', 'regla', 'estado', 'creada_en', 'resuelta_en')
    list_filter = ('estado', 'tipo', 'regla', 'device__tipo')
    search_fields = ('device__nombre', 'titulo', 'texto')
    list_select_related = ('device',)
    readonly_fields = ('device', 'regla', 'sys_error', 'creada_en', 'resuelta_en')


@admin.register(OIDmetric)
class OIDmetricAdmin(admin.ModelAdmin):
    list_display = ('marca', 'tipo', 'descripcion', 'codigos')
    list_filter = ('marca__nombre', 'tipo')
    search_fields = ('marca__nombre', 'marca__modelo', 'tipo')
    list_select_related = ('marca',)

@admin.register(DeviceLatencyHistory)
class DeviceLatency(admin.ModelAdmin):
    list_display = ('device', 'latency_ms', 'success', 'timestamp')
    date_hierarchy = 'timestamp'
    search_fields = ('device__nombre',)
    readonly_fields = ('device',)

@admin.register(InterfaceMetricHistory)
class InterfaceMetrica(admin.ModelAdmin):
    list_display = ('interfaz', 'timestamp', 'rx', 'tx')
    search_fields = ('interfaz__nombre', 'interfaz__nombre2', 'interfaz__dispositivo__nombre')
    readonly_fields = ('interfaz',)