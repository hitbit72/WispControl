from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Información WISP', {'fields': ('rol', 'telefono', 'activo_en_campo')}),
    )
