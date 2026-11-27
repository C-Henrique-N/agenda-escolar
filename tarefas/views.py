import json
from datetime import datetime, timedelta
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from .models import (
    Materia,
    Tarefa,
    HorarioAula,
    Perfil,
    RankPresente,
    RANKS_TABELA,
    calcular_ranking_por_pontos,
    usuario_tem_acesso_admin,
    avaliar_conquistas,
)
from .forms import TarefaForm, CadastroForm


def _url_segura(campo_imagem):
    try:
        if campo_imagem and getattr(campo_imagem, "name", None):
            return campo_imagem.url
    except Exception:
        return ""
    return ""


EXTENSOES_BANNER_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".ogg"}
TAMANHO_MAX_BANNER = 50 * 1024 * 1024  # 50 MB


def _banner_e_video(campo):
    try:
        return bool(campo and Path(campo.name).suffix.lower() in {".mp4", ".webm", ".ogg"})
    except Exception:
        return False


def _calcular_pontos_usuario(tarefas_qs):
    # Cada tarefa concluída vale exatamente 50 XP.
    return tarefas_qs.filter(concluida=True).count() * 50


def _formatar_tempo_segundos(segundos: int) -> str:
    segundos = max(0, int(segundos or 0))
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    return f"{horas}h {minutos:02d}min"


def _registrar_dia_ativo(perfil: Perfil):
    hoje_str = timezone.localdate().isoformat()
    dias = list(perfil.dias_logados or [])
    if hoje_str not in dias:
        dias.append(hoje_str)
        perfil.dias_logados = dias
        perfil.save(update_fields=["dias_logados"])
    return len(dias)


def _montar_estatisticas_e_ranking(user, tarefas_qs, materias_qs, perfil):
    hoje = timezone.localdate()
    concluidas_qs = tarefas_qs.filter(concluida=True)
    total_count = tarefas_qs.count()
    concluidas_count = concluidas_qs.count()
    tarefas_hoje_count = tarefas_qs.filter(data=hoje).count()
    produtividade_pct = int(round((concluidas_count / total_count) * 100)) if total_count else 0

    pontos = _calcular_pontos_usuario(tarefas_qs)
    ranking = calcular_ranking_por_pontos(pontos, user=user)
    tempo_segundos = int(perfil.tempo_ativo_segundos or 0)
    tempo_focado_str = _formatar_tempo_segundos(tempo_segundos)
    horas_progresso_pct = min(100, int(round((tempo_segundos / 7200) * 100)))
    pontos_progresso_pct = min(100, int(round((pontos / 15000) * 100)))

    datas_concluidas = set(concluidas_qs.values_list("data", flat=True))
    sequencia = 0
    cursor = hoje
    while cursor in datas_concluidas:
        sequencia += 1
        cursor -= timedelta(days=1)

    dias_ativos = _registrar_dia_ativo(perfil)
    conquistas = avaliar_conquistas(concluidas_count, dias_ativos, tempo_segundos)

    inicio_semana = hoje - timedelta(days=hoje.weekday())
    nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    progresso_semanal = []
    melhor_dia_nome = "Domingo"
    melhor_dia_pct = 0
    for i in range(7):
        dia_alvo = inicio_semana + timedelta(days=i)
        do_dia = tarefas_qs.filter(data=dia_alvo)
        tot_d = do_dia.count()
        conc_d = do_dia.filter(concluida=True).count()
        pct_d = int(round((conc_d / tot_d) * 100)) if tot_d else 0
        progresso_semanal.append({"label": nomes_dias[i], "pct": pct_d, "concluidas": conc_d, "total": tot_d})
        if pct_d >= melhor_dia_pct:
            melhor_dia_pct = pct_d
            melhor_dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][i]

    cont_tarefa = tarefas_qs.filter(tipo="Tarefa").count()
    cont_trabalho = tarefas_qs.filter(tipo="Trabalho").count()
    cont_prova = tarefas_qs.filter(tipo="Prova").count()
    soma_tipos = max(1, cont_tarefa + cont_trabalho + cont_prova)
    categorias_stats = [
        {"nome": "Tarefas", "pct": int(round((cont_tarefa / soma_tipos) * 100)) if total_count else 0, "cor": "#8b5cf6"},
        {"nome": "Trabalhos", "pct": int(round((cont_trabalho / soma_tipos) * 100)) if total_count else 0, "cor": "#a855f7"},
        {"nome": "Provas", "pct": int(round((cont_prova / soma_tipos) * 100)) if total_count else 0, "cor": "#c084fc"},
        {"nome": "Matérias", "pct": min(100, materias_qs.count() * 15), "cor": "#9d4edd"},
    ]

    # Exibe somente contas cadastradas pelo fluxo oficial do site.
    # Contas antigas/de teste sem Perfil não entram no ranking.
    todos_usuarios = list(
        User.objects.filter(is_active=True, perfil__isnull=False).order_by("id")
    )
    perfis_map = {p.user_id: p for p in Perfil.objects.filter(user__in=todos_usuarios)}
    leaderboard_raw = []
    for u in todos_usuarios:
        u_tarefas = Tarefa.objects.filter(usuario=u)
        u_pontos = _calcular_pontos_usuario(u_tarefas)
        u_rank = calcular_ranking_por_pontos(u_pontos, user=u)
        u_perfil = perfis_map.get(u.id)
        leaderboard_raw.append({
            "user_id": u.id, "username": u.username, "pontos": u_pontos,
            "concluidas": u_tarefas.filter(concluida=True).count(),
            "rank_slug": u_rank["rank_slug"], "rank_nome": u_rank["rank_nome"],
            "rank_imagem": u_rank["rank_imagem"], "rank_presenteado": u_rank["rank_presenteado"],
            "rank_obtivel": u_rank["rank_obtivel"],
            "foto_url": _url_segura(getattr(u_perfil, "foto_perfil", None)),
            "is_current": u.id == user.id,
        })
    leaderboard_raw.sort(key=lambda item: (-item["pontos"], -item["concluidas"], item["user_id"]))
    for idx, item in enumerate(leaderboard_raw, start=1):
        item["posicao"] = idx

    presentes_ativos = []
    try:
        for rp in RankPresente.objects.select_related("usuario").order_by("-atualizado_em"):
            presentes_ativos.append({"id": rp.id, "username": rp.usuario.username, "rank_slug": rp.rank_slug, "concedido_por": rp.concedido_por})
    except Exception:
        presentes_ativos = []

    return {
        "hoje_iso": hoje.isoformat(), "total_tarefas_count": total_count,
        "tarefas_concluidas_count": concluidas_count, "tarefas_hoje_count": tarefas_hoje_count,
        "produtividade_pct": produtividade_pct, "tempo_ativo_segundos": tempo_segundos,
        "tempo_focado_str": tempo_focado_str, "horas_progresso_pct": horas_progresso_pct,
        "pontos_progresso_pct": pontos_progresso_pct, "sequencia_dias": sequencia,
        "dias_ativos": dias_ativos, "conquistas": conquistas,
        "melhor_dia_nome": melhor_dia_nome, "melhor_dia_pct": melhor_dia_pct,
        "progresso_semanal": progresso_semanal, "categorias_stats": categorias_stats,
        "ranking": ranking, "ranks_tabela": RANKS_TABELA, "leaderboard": leaderboard_raw,
        "top1_usuario": leaderboard_raw[0] if leaderboard_raw else None,
        "todos_usuarios": todos_usuarios, "pode_presentear_rank": usuario_tem_acesso_admin(user),
        "presentes_ativos": presentes_ativos,
    }


def _parse_data_segura(valor_data):
    if not valor_data:
        return timezone.localdate()
    try:
        return datetime.strptime(str(valor_data).strip(), "%Y-%m-%d").date()
    except ValueError:
        return timezone.localdate()


def _parse_horario_seguro(valor_horario):
    if not valor_horario:
        return datetime.strptime("19:00", "%H:%M").time()
    texto = str(valor_horario).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(texto, fmt).time()
        except ValueError:
            continue
    return datetime.strptime("19:00", "%H:%M").time()


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required
def dashboard_escolar(request):
    materias = Materia.objects.filter(usuario=request.user)
    # Mantém todas as tarefas no banco para preservar histórico e XP,
    # mas exibe nas listas somente as tarefas de hoje ou de datas futuras.
    tarefas_historico = Tarefa.objects.filter(usuario=request.user)
    hoje = timezone.localdate()
    tarefas = tarefas_historico.filter(data__gte=hoje).order_by('concluida', 'data', 'horario', '-id')
    horarios = HorarioAula.objects.filter(usuario=request.user)
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # A troca de senha precisa ser identificada antes dos demais formulários
        # da dashboard, para não ser confundida com uma atualização de perfil.
        if 'alterar_senha' in request.POST:
            senha_atual = request.POST.get('senha_atual') or ''
            nova_senha = (request.POST.get('nova_senha') or '').strip()
            confirmar_senha = (request.POST.get('confirmar_senha') or '').strip()

            if not request.user.check_password(senha_atual):
                messages.error(request, 'A senha atual está incorreta.')
                return redirect('dashboard')
            if len(nova_senha) < 6:
                messages.error(request, 'A nova senha deve ter pelo menos 6 caracteres.')
                return redirect('dashboard')
            if nova_senha != confirmar_senha:
                messages.error(request, 'A confirmação da nova senha não confere.')
                return redirect('dashboard')

            request.user.set_password(nova_senha)
            request.user.save(update_fields=['password'])
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('dashboard')

        if 'presentear_rank' in request.POST:
            if not usuario_tem_acesso_admin(request.user):
                messages.error(request, 'Apenas AkiiraPW e contas autorizadas podem presentear ranks.')
                return redirect('dashboard')
            alvo_id = request.POST.get('usuario_alvo')
            rank_slug = (request.POST.get('rank_slug') or '').strip().lower()
            alvo = User.objects.filter(id=alvo_id).first()
            slugs_validos = {c[0] for c in RankPresente.RANK_CHOICES}
            if alvo and rank_slug in slugs_validos:
                RankPresente.objects.update_or_create(
                    usuario=alvo,
                    defaults={
                        'rank_slug': rank_slug,
                        'concedido_por': request.user.username,
                    }
                )
                messages.success(request, f'Rank "{rank_slug}" presenteado para {alvo.username}!')
            return redirect('dashboard')

        elif 'remover_presente_rank' in request.POST:
            if not usuario_tem_acesso_admin(request.user):
                messages.error(request, 'Apenas AkiiraPW e contas autorizadas podem remover ranks presenteados.')
                return redirect('dashboard')
            alvo_id = request.POST.get('usuario_alvo')
            if alvo_id:
                RankPresente.objects.filter(usuario_id=alvo_id).delete()
                messages.success(request, 'Rank presenteado removido.')
            return redirect('dashboard')

        elif 'cadastrar_materia' in request.POST:
            nome = (request.POST.get('nome') or '').strip()
            professor = (request.POST.get('professor') or '').strip()
            if nome:
                Materia.objects.create(
                    nome=nome,
                    professor=professor,
                    usuario=request.user
                )
                messages.success(request, 'Matéria cadastrada com sucesso!')
            return redirect('dashboard')

        elif 'cadastrar_horario' in request.POST:
            dia = request.POST.get('dia_semana')
            inicio = _parse_horario_seguro(request.POST.get('horario_inicio'))
            materia_id = request.POST.get('materia')
            materia = Materia.objects.filter(id=materia_id, usuario=request.user).first()
            if dia and materia:
                HorarioAula.objects.create(
                    dia_semana=dia,
                    horario_inicio=inicio,
                    materia=materia,
                    usuario=request.user
                )
                messages.success(request, 'Horário adicionado com sucesso!')
            return redirect('dashboard')

        elif 'cadastrar_tarefa' in request.POST or 'titulo' in request.POST:
            titulo = (request.POST.get('titulo') or '').strip()[:100]
            descricao = (request.POST.get('descricao') or '').strip()[:500]
            data = _parse_data_segura(request.POST.get('data'))
            horario = _parse_horario_seguro(request.POST.get('horario'))
            prioridade = request.POST.get('prioridade') or 'média'
            categoria = (request.POST.get('categoria') or '').strip()
            tipo = request.POST.get('tipo') or categoria or 'Tarefa'
            materia_id = request.POST.get('materia')
            materia = Materia.objects.filter(id=materia_id, usuario=request.user).first() if materia_id else None

            if titulo:
                Tarefa.objects.create(
                    titulo=titulo,
                    descricao=descricao,
                    data=data,
                    horario=horario,
                    prioridade=prioridade,
                    tipo=tipo,
                    materia=materia,
                    usuario=request.user
                )
                messages.success(request, 'Tarefa adicionada com sucesso!')
            return redirect('dashboard')

        perfil_alterado = False
        novo_username = (request.POST.get('username') or '').strip()
        novo_email = request.POST.get('email')
        nova_bio = request.POST.get('bio')
        novo_sobre = request.POST.get('sobre')

        if novo_email is not None:
            email_limpo = novo_email.strip()
            if email_limpo != (request.user.email or ''):
                request.user.email = email_limpo
                request.user.save()
                perfil_alterado = True

        if novo_username and novo_username != request.user.username:
            if User.objects.filter(username=novo_username).exclude(pk=request.user.pk).exists():
                messages.error(request, 'Este nome de usuário já está em uso.')
                return redirect('dashboard')
            try:
                request.user.username = novo_username
                request.user.save()
                perfil_alterado = True
            except IntegrityError:
                messages.error(request, 'Não foi possível atualizar o nome de usuário.')
                return redirect('dashboard')

        if nova_bio is not None:
            perfil.bio = nova_bio.strip()[:160]
            perfil_alterado = True
        if novo_sobre is not None:
            perfil.sobre = novo_sobre.strip()
            perfil_alterado = True
        if 'foto_perfil' in request.FILES:
            perfil.foto_perfil = request.FILES['foto_perfil']
            perfil_alterado = True
        if 'imagem_fundo' in request.FILES:
            arquivo_banner = request.FILES['imagem_fundo']
            extensao = Path(arquivo_banner.name).suffix.lower()
            if extensao not in EXTENSOES_BANNER_PERMITIDAS:
                messages.error(request, 'Formato inválido. Use JPG, PNG, WEBP, GIF, MP4, WEBM ou OGG.')
                return redirect('dashboard')
            if arquivo_banner.size > TAMANHO_MAX_BANNER:
                messages.error(request, 'O banner deve ter no máximo 50 MB.')
                return redirect('dashboard')
            perfil.imagem_fundo = arquivo_banner
            perfil_alterado = True

        if perfil_alterado:
            perfil.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('dashboard')

    stats = _montar_estatisticas_e_ranking(request.user, tarefas_historico, materias, perfil)

    contexto = {
        'materias': materias,
        'tarefas': tarefas,
        'horarios': horarios,
        'perfil': perfil,
        'foto_perfil_url': _url_segura(getattr(perfil, 'foto_perfil', None)),
        'imagem_fundo_url': _url_segura(getattr(perfil, 'imagem_fundo', None)),
        'imagem_fundo_is_video': _banner_e_video(getattr(perfil, 'imagem_fundo', None)),
        **stats,
    }
    return render(request, 'tarefas/dashboard.html', contexto)


@login_required
@require_POST
def excluir_tarefa(request, id):
    tarefa = get_object_or_404(Tarefa, id=id, usuario=request.user)
    tarefa.delete()
    return redirect('dashboard')


@login_required
def concluir_tarefa(request, id):
    tarefa = get_object_or_404(Tarefa, id=id, usuario=request.user)
    tarefa.concluida = not tarefa.concluida
    tarefa.save(update_fields=["concluida"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        tarefas_qs = Tarefa.objects.filter(usuario=request.user)
        total = tarefas_qs.count()
        concluidas = tarefas_qs.filter(concluida=True).count()
        perfil, _ = Perfil.objects.get_or_create(user=request.user)
        dias_ativos = _registrar_dia_ativo(perfil)
        pontos = concluidas * 50
        ranking = calcular_ranking_por_pontos(pontos, user=request.user)
        return JsonResponse({
            "ok": True, "concluida": tarefa.concluida,
            "concluidas_count": concluidas, "total_count": total,
            "produtividade_pct": int(round((concluidas / total) * 100)) if total else 0,
            "pontos": pontos, "rank_nome": ranking["rank_nome"],
            "conquistas": avaliar_conquistas(concluidas, dias_ativos, perfil.tempo_ativo_segundos),
        })
    return redirect('dashboard')


@login_required
@require_POST
def registrar_tempo_atividade(request):
    try:
        dados = json.loads(request.body.decode("utf-8") or "{}")
        delta = int(dados.get("segundos", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        delta = 0
    delta = max(0, min(delta, 120))
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    dias_ativos = _registrar_dia_ativo(perfil)
    if delta:
        perfil.tempo_ativo_segundos = (perfil.tempo_ativo_segundos or 0) + delta
        perfil.save(update_fields=["tempo_ativo_segundos"])
    tarefas_concluidas = Tarefa.objects.filter(usuario=request.user, concluida=True).count()
    return JsonResponse({
        "ok": True, "tempo_ativo_segundos": perfil.tempo_ativo_segundos,
        "tempo_focado_str": _formatar_tempo_segundos(perfil.tempo_ativo_segundos),
        "conquistas": avaliar_conquistas(tarefas_concluidas, dias_ativos, perfil.tempo_ativo_segundos),
    })


@login_required
def editar_tarefa(request, id):
    tarefa = get_object_or_404(Tarefa, id=id, usuario=request.user)
    if request.method == 'POST':
        form = TarefaForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TarefaForm(instance=tarefa)
    return render(request, 'tarefas/editar_tarefa.html', {'form': form, 'tarefa': tarefa})


@login_required
def perfil_usuario(request):
    return redirect('dashboard')


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