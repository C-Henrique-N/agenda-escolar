from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .models import Materia, Tarefa, HorarioAula, Perfil
from .forms import TarefaForm, CadastroForm


@login_required
def home(request):
    if request.method == "POST":
        form = TarefaForm(request.POST)

        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.usuario = request.user
            tarefa.save()
            return redirect("home")
    else:
        form = TarefaForm()

    filtro = request.GET.get('status')

    tarefas = Tarefa.objects.filter(usuario=request.user)

    if filtro == "pendentes":
        tarefas = tarefas.filter(concluida=False)
    elif filtro == "concluidas":
        tarefas = tarefas.filter(concluida=True)

    tarefas = tarefas.order_by('data', 'horario')

    return render(
        request,
        "tarefas/home.html",
        {"tarefas": tarefas, "form": form}
    )


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
    else:
        form = TarefaForm(instance=tarefa)

    tarefas = Tarefa.objects.filter(usuario=request.user)

    return render(
        request,
        "tarefas/home.html",
        {"form": form, "tarefas": tarefas}
    )


@login_required
def dashboard_escolar(request):
    materias = Materia.objects.filter(usuario=request.user)
    tarefas = Tarefa.objects.filter(usuario=request.user)
    horarios = HorarioAula.objects.filter(usuario=request.user)
    
    # Garante que o perfil existe para carregar a foto e o fundo no dashboard
    perfil, created = Perfil.objects.get_or_create(user=request.user)

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
                # Limita e garante que o ano tenha no máximo 4 dígitos (evita o erro do navegador)
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
    # Garante que o usuário logado possui um Perfil criado no banco
    perfil, created = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        novo_username = request.POST.get('username')
        if novo_username:
            request.user.username = novo_username
            request.user.save()

        if 'foto_perfil' in request.FILES:
            perfil.foto_perfil = request.FILES['foto_perfil']
        if 'imagem_fundo' in request.FILES:
            perfil.imagem_fundo = request.FILES['imagem_fundo']
        
        perfil.save()
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
            login(request, user)
            return redirect("dashboard")
    else:
        form = CadastroForm()

    return render(
        request,
        "tarefas/cadastro.html",
        {"form": form}
    )