from django.urls import path
from . import views
from .views import LoginUsuario
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard_escolar, name='dashboard'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path("login/", LoginUsuario.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path('excluir/<int:id>/', views.excluir_tarefa, name='excluir_tarefa'),
    path('concluir/<int:id>/', views.concluir_tarefa, name='concluir_tarefa'),
    path('editar/<int:id>/', views.editar_tarefa, name='editar_tarefa'),
    path('api/registrar-tempo/', views.registrar_tempo_atividade, name='registrar_tempo_atividade'),
]