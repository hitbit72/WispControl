from django.urls import path

from . import views

app_name = 'dispositivos'

urlpatterns = [
    # Dispositivos
    path('', views.lista_dispositivos, name='lista'),
    path('nuevo/', views.nuevo_dispositivo, name='nuevo'),
    path('<int:pk>/nuevo/', views.nuevo_dispositivo, name='nuevo_dispositivo'),
    path('<int:pk>/', views.detalle_dispositivo, name='detalle'),
    path('<int:pk>/editar/', views.editar_dispositivo, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_dispositivo, name='eliminar'),
    # Interfaces
    path('<int:dispositivo_pk>/interfaces/nuevo/', views.nueva_interfaz, name='nueva_interfaz'),
    path('interfaces/<int:pk>/editar/', views.editar_interfaz, name='editar_interfaz'),
    path('interfaces/<int:pk>/eliminar/', views.eliminar_interfaz, name='eliminar_interfaz'),
    # Enlaces
    path('<int:dispositivo_pk>/enlaces/nuevo/', views.nuevo_enlace, name='nuevo_enlace'),
    path('enlaces/<int:pk>/editar/', views.editar_enlace, name='editar_enlace'),
    path('enlaces/<int:pk>/eliminar/', views.eliminar_enlace, name='eliminar_enlace'),
    path('interfaces/opciones/', views.opciones_interfaces_dispositivo, name='opciones_interfaces_dispositivo'),
]
