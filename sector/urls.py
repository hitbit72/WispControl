from django.urls import path

from . import views

app_name = 'sectores'

urlpatterns = [
    # Sectores
    path('', views.lista_sectores, name='lista'),
    path('nuevo/', views.form_sector, name='nuevo'),
    path('<int:pk>/', views.detalle_sector, name='detalle'),
    path('<int:pk>/editar/', views.form_sector, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_sector, name='eliminar'),
]
