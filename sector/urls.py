from django.urls import path

from . import views

app_name = 'sectores'

urlpatterns = [
    # Sectores
    path('', views.lista_sectores, name='lista'),
    path('sectores/nuevo/', views.form_sector, name='nuevo_sector'),
    path('sectores/<int:pk>/', views.detalle_sector, name='detalle_sector'),
    path('sectores/<int:pk>/editar/', views.form_sector, name='editar_sector'),
    path('sectores/<int:pk>/eliminar/', views.eliminar_sector, name='eliminar_sector'),
]
