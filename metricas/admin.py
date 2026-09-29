from django.contrib import admin

from .models import Alarma, DeviceMetrics, OIDmetric, DeviceLatencyHistory


@admin.register(DeviceMetrics)
class DeviceMetricsAdmin(admin.ModelAdmin):
    list_display = ('device', 'status', 'status_ping', 'cpu', 'ram', 'frequency', 'clients', 'timeping')
    list_filter = ('status', 'status_ping', 'device__tipo', 'device__marca')
    date_hierarchy = 'timestamp'
    search_fields = ('device__nombre',)
    readonly_fields = ('device', 'timestamp', 'timescan', 'timeping')
    list_select_related = ('device',)


@admin.register(Alarma)
class AlarmaAdmin(admin.ModelAdmin):
    list_display = ('device', 'titulo', 'tipo', 'regla', 'estado', 'creada_en', 'resuelta_en')
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
    list_filter = ('device',)
    date_hierarchy = 'timestamp'
    search_fields = ('device__nombre',)
    readonly_fields = ('device',)