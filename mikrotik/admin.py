from django import forms
from django.contrib import admin

from .models import Router, Plan
from core.fields import EncryptedCharField


class PlanInline(admin.TabularInline):
    model = Plan
    extra = 0


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'modelo', 'ip', 'puerto', 'sector')
    list_filter = ('sector',)
    search_fields = ('nombre', 'ip', 'modelo')
    inlines = [PlanInline]
    formfield_overrides = {
        EncryptedCharField: {'widget': forms.PasswordInput(render_value=True)},
    }


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'router', 'velocidad_bajada', 'velocidad_subida', 'priority_down', 'priority_up')
    list_filter = ('router',)
    search_fields = ('nombre', 'router__nombre')
