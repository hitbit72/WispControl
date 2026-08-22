from django.urls import path

from . import views

app_name = 'dispositivos'

urlpatterns = [
    # Dispositivos
    path('', views.lista_dispositivos, name='lista'),
    path('nuevo/', views.nuevo_dispositivo, name='nuevo_dispositivo'),
    path('sectores/<int:sector_pk>/nuevo/', views.nuevo_dispositivo_sector, name='nuevo_dispositivo_sector'),
    path('clientes/<int:cliente_pk>/nuevo/', views.nuevo_dispositivo_cliente, name='nuevo_dispositivo_cliente'),
    path('<int:pk>/', views.detalle_dispositivo, name='detalle_dispositivo'),
    path('<int:pk>/editar/', views.editar_dispositivo, name='editar_dispositivo'),
    path('clientes/<int:pk>/editar/', views.editar_dispositivo_cliente, name='editar_dispositivo_cliente'),
    path('sectores/<int:pk>/editar/', views.editar_dispositivo_sector, name='editar_dispositivo_sector'),
    path('<int:pk>/eliminar/', views.eliminar_dispositivo, name='eliminar_dispositivo'),
]
