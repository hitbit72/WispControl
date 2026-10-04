from django.contrib import admin
from .models import Marca, TipoEquipo, Dispositivo, Interfaz, Enlace


class InterfazInline(admin.TabularInline):
    model = Interfaz
    extra = 0

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'modelo')
    list_filter = ('nombre',)
    search_fields = ('nombre', 'modelo')


@admin.register(TipoEquipo)
class TipoEquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'clave')
    list_filter = ('nombre',)
    search_fields = ('nombre', 'clave')


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ('ip_gestion','nombre', 'nombre_host', 'rol', 'tipo', 'marca', 'sector', 'estado', 'cliente')
    list_filter = ('rol','tipo', 'marca', 'estado', 'sector')
    search_fields = ('nombre', 'ip_gestion', 'mac_address', 'cliente', 'tipo__nombre')
    inlines = [InterfazInline]


@admin.register(Interfaz)
class InterfazAdmin(admin.ModelAdmin):
    list_display = ('dispositivo', 'nombre', 'nombre2', 'mostrar', 'tipo', 'estado', 'velocidad_mbps', 'ip_address')
    list_filter = ('tipo', 'estado')
    search_fields = ('nombre', 'nombre2', 'dispositivo__nombre', 'ip_address')
    readonly_fields = ('dispositivo',)

@admin.register(Enlace)
class EnlaceAdmin(admin.ModelAdmin):
    list_display = ('dispositivo_origen', 'dispositivo_destino', 'tipo', 'ancho_banda_mbps')
    list_filter = ('tipo',)
