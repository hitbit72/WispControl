from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('mikrotik/', include('mikrotik.urls')),
    path('sectores/', include('sector.urls')),
    path('dispositivos/', include('dispositivos.urls')),
    path('eventos/', include('eventos.urls')),
    path('clientes/', include('clientes.urls')),
]

# Manejo de archivos estáticos media en modo de desarrollo
# En un entorno de producción no es necesario, ya que se manejan de forma diferente.
if  settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.MEDIA_ROOT)  # Manejo de archivos media en modo de desarrollo
