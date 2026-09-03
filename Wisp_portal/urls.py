from django.contrib import admin
from django.urls import path, include
from django.conf import settings


admin.site.site_header = "InforCEM"
admin.site.index_title = "Panel de administrador"
admin.site.site_title = "InforCEM"

urlpatterns = [
    path('', include('accounts.urls')),
    # path de auth
    path('accounts/', include('django.contrib.auth.urls')),  # Manejo de autenticación
    path('admin/', admin.site.urls),
    path('mikrotik/', include('mikrotik.urls')),
    path('sectores/', include('sector.urls')),
    path('dispositivos/', include('dispositivos.urls')),
    path('eventos/', include('eventos.urls')),
    path('clientes/', include('clientes.urls')),
]

# Manejo de archivos estáticos en modo de desarrollo
# En un entorno de producción no es necesario, ya que se manejan de forma diferente.
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])