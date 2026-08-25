from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('mikrotik/', include('mikrotik.urls')),
    path('sectores/', include('sector.urls')),
    path('dispositivos/', include('dispositivos.urls')),
    path('eventos/', include('eventos.urls')),
    path('clientes/', include('clientes.urls')),
]
