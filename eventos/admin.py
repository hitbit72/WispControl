from django.contrib import admin
from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Solo lectura: los eventos se generan desde los módulos, nunca a mano.
    Modificación: desde el administración DJango si se pueden modificar"""
    list_display = ('fecha', 'nivel', 'titulo', 'modulo', 'leido', 'user')
    list_filter = ('nivel', 'leido', 'modulo')
    search_fields = ('titulo', 'texto', 'modulo')
    readonly_fields = ('fecha', 'nivel', 'modulo', 'user')

