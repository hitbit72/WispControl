from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = 'accounts'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=LoginForm,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('contrasena/', views.CambiarContrasenaView.as_view(), name='cambiar_contrasena'),
    path('contrasena/cambiada/', views.CambiarContrasenaOkView.as_view(), name='cambiar_contrasena_ok'),
]