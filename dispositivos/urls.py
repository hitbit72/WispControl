from django.urls import path

from . import views

app_name = 'dispositivos'

urlpatterns = [
    # Dispositivos
    path('', views.lista_dispositivos, name='lista'),
    path('0/nuevo/', views.nuevo_dispositivo, name='nuevo'),
    path('<int:pk>/nuevo/', views.nuevo_dispositivo, name='nuevo_dispositivo'),
    path('<int:pk>/', views.detalle_dispositivo, name='detalle'),
    path('<int:pk>/editar/', views.editar_dispositivo, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_dispositivo, name='eliminar'),
]
