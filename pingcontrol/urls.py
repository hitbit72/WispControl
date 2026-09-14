from django.urls import path
from . import views

app_name = 'pingcontrol'

urlpatterns = [
    path('dispositivo/<int:pk>/ping/', views.ping_dispositivo, name='ping_dispositivo'),
]