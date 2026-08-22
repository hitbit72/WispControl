from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('mikrotik/', include('mikrotik.urls')),
    path('sector/', include('sector.urls')),
    path('eventos/', include('eventos.urls')),
]
