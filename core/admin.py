from django.contrib import admin
from .models import Provincia, Poblacion

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Poblacion)
class PoblacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia',)
    search_fields = ('nombre', 'provincia__nombre',)
