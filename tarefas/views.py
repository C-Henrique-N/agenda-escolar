from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from .models import Materia, Tarefa, HorarioAula, Perfil
from .forms import TarefaForm, CadastroForm


@login_required
def home(request):
    return redirect("dashboard")


@login_required
def excluir_tarefa(request, id):
    tarefa = get_object_or_404(
        Tarefa,
        id=id,
        usuario=request.user
    )
    tarefa.delete()
    return redirect("dashboard")


@login_required
def concluir_tarefa(request, id):
    tarefa = get_object_or_404(
        Tarefa,
        id=id,
        usuario=request.user
    )
    tarefa.concluida = True
    tarefa.save()
    return redirect("dashboard")


@login_required
def editar_tarefa(request, id):
    tarefa = get_object_or_404(
        Tarefa,
        id=id,
        usuario=request.user
    )

    if request.method == "POST":
        form = TarefaForm(request.POST, instance=tarefa)

        if form.is_valid():
            form.save()
            return redirect("dashboard")

    return redirect("dashboard")


@login_required
def dashboard_escolar(request):
    materias = Materia.objects.filter(usuario=request.user)
    tarefas = Tarefa.objects.filter(usuario=request.user)
    horarios = HorarioAula.objects.filter(usuario=request.user)

    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':

        if 'cadastrar_materia' in request.POST:
            nome = request.POST.get('nome')
            professor = request.POST.get('professor')

            if nome:
                Materia.objects.create(
                    nome=nome,
                    professor=professor,
                    usuario=request.user
                )

            return redirect('dashboard')

        elif 'cadastrar_tarefa' in request.POST:
            titulo = request.POST.get('titulo')
            tipo = request.POST.get('tipo')
            materia_id = request.POST.get('materia')
            data = request.POST.get('data')
            horario = request.POST.get('horario') or None
            prioridade = request.POST.get('prioridade')

            materia = None

            if materia_id:
                materia = get_object_or_404(
                    Materia,
                    id=materia_id,
                    usuario=request.user
                )

            if titulo and data:
                partes = data.split('-')
                if len(partes) > 0 and partes[0]:
                    partes[0] = partes[0][-4:]
                data = '-'.join(partes)

                Tarefa.objects.create(
                    titulo=titulo,
                    tipo=tipo,
                    materia=materia,
                    data=data,
                    horario=horario,
                    prioridade=prioridade,
                    usuario=request.user
                )

            return redirect('dashboard')

    context = {
        'materias': materias,
        'tarefas': tarefas.order_by('data', 'horario'),
        'horarios': horarios,
        'perfil': perfil,
    }

    return render(
        request,
        'tarefas/dashboard.html',
        context
    )


@login_required
def perfil_usuario(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        novo_username = (request.POST.get('username') or '').strip()

        if novo_username and novo_username != request.user.username:
            if User.objects.filter(username=novo_username).exclude(pk=request.user.pk).exists():
                messages.error(request, 'Este nome de usuário já está em uso.')
                return redirect('perfil')
            try:
                request.user.username = novo_username
                request.user.save()
            except IntegrityError:
                messages.error(request, 'Não foi possível atualizar o nome de usuário.')
                return redirect('perfil')

        if 'foto_perfil' in request.FILES:
            perfil.foto_perfil = request.FILES['foto_perfil']
        if 'imagem_fundo' in request.FILES:
            perfil.imagem_fundo = request.FILES['imagem_fundo']

        perfil.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('perfil')

    return render(
        request,
        'tarefas/perfil.html',
        {'perfil': perfil}
    )


class LoginUsuario(LoginView):
    template_name = "tarefas/login.html"
    redirect_authenticated_user = True


def cadastro(request):
    if request.method == "POST":
        form = CadastroForm(request.POST)

        if form.is_valid():
            user = form.save()
            Perfil.objects.get_or_create(user=user)
            login(request, user)
            return redirect("dashboard")
    else:
        form = CadastroForm()

    return render(
        request,
        "tarefas/cadastro.html",
        {"form": form}
    )
