from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('mikrotik/', include('mikrotik.urls')),
    path('sector/', include('sector.urls')),
    path('dispositivo/', include('dispositivos.urls')),
    path('eventos/', include('eventos.urls')),
    path('cliente/', include('clientes.urls')),
]
