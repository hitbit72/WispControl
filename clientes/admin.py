from django.contrib import admin
from .models import Cliente, Contrato, CuentaBancaria


class ContratoInline(admin.TabularInline):
    model = Contrato
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'apodo', 'telefono', 'poblacion', 'activo', 'fecha_alta')
    list_filter = ('activo', 'poblacion')
    search_fields = ('nombre_completo', 'apodo', 'numero_documento', 'telefono', 'email')
    inlines = [ContratoInline]


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cliente', 'plan', 'conexion', 'estado', 'precio_mensual')
    list_filter = ('estado', 'conexion', 'plan__router')
    search_fields = ('nombre', 'cliente__nombre_completo', 'plan__nombre', 'identificador_mikrotik', 'ip_asignada')


@admin.register(CuentaBancaria)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cliente')
    list_filter = ('nombre', 'cliente__nombre_completo')
    search_fields = ('ombre', 'cliente__nombre_completo')