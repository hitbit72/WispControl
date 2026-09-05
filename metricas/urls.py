from django.urls import path

from . import views

app_name = 'metricas'

urlpatterns = [
    path('dispositivo/<int:pk>/actualizar-snmp/', views.actualizar_metricas_snmp, name='actualizar_snmp'),
]