from django.contrib import admin
from .models import Sector

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre','poblacion',)
    search_fields = ('nombre','poblacion__nombre',)


