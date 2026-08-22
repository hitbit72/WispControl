from django.urls import path

from . import views

app_name = 'mikrotik'

urlpatterns = [
    path('', views.lista_routers, name='lista'),
    path('nuevo/', views.form_router, name='nuevo'),
    path('<int:pk>/', views.detalle_router, name='detalle'),
    path('<int:pk>/editar/', views.form_router, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_router, name='eliminar'),
    path('<int:router_pk>/planes/nuevo/', views.nuevo_plan, name='nuevo_plan'),
    path('planes/<int:pk>/editar/', views.editar_plan, name='editar_plan'),
    path('planes/<int:pk>/eliminar/', views.eliminar_plan, name='eliminar_plan'),
]
