from django.urls import path

from . import views

app_name = 'eventos'

urlpatterns = [
    path('', views.lista_eventos, name='lista'),
    path('marcar-todos/', views.marcar_todos_leidos, name='marcar_todos_leidos'),
    path('<int:pk>/leido/', views.marcar_leido, name='marcar_leido'),
]