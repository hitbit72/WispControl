from django.urls import path

from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.lista_clientes, name='lista'),
    path('nuevo/', views.form_cliente, name='nuevo'),
    path('<int:pk>/', views.detalle_cliente, name='detalle'),
    path('<int:pk>/editar/', views.form_cliente, name='editar'),
    path('<int:pk>/activar/', views.alternar_activo_cliente, name='alternar_activo'),
    path('<int:cliente_pk>/contratos/nuevo/', views.nuevo_contrato, name='nuevo_contrato'),
    path('contratos/<int:pk>/editar/', views.editar_contrato, name='editar_contrato'),
    path('contratos/<int:pk>/eliminar/', views.eliminar_contrato, name='eliminar_contrato'),
]
