from django.db import models
from django.contrib.auth.models import User


RANKS_OBTIVEIS = [
    {
        "slug": "bronze",
        "nome": "Bronze",
        "faixa_pontos": "0 - 1.000 pontos",
        "min_pontos": 0,
        "imagem": "tarefas/ranks/bronze.png",
        "desc": "Você está começando!",
        "obtivel": True,
    },
    {
        "slug": "prata",
        "nome": "Prata",
        "faixa_pontos": "1.000 - 2.499 pontos",
        "min_pontos": 1000,
        "imagem": "tarefas/ranks/prata.png",
        "desc": "Continue assim!",
        "obtivel": True,
    },
    {
        "slug": "ouro",
        "nome": "Ouro",
        "faixa_pontos": "2.500 - 4.499 pontos",
        "min_pontos": 2500,
        "imagem": "tarefas/ranks/ouro.png",
        "desc": "Você faz a diferença!",
        "obtivel": True,
    },
    {
        "slug": "platina",
        "nome": "Platina",
        "faixa_pontos": "4.500 - 6.999 pontos",
        "min_pontos": 4500,
        "imagem": "tarefas/ranks/platina.png",
        "desc": "Você se destaca!",
        "obtivel": True,
    },
    {
        "slug": "diamante",
        "nome": "Diamante",
        "faixa_pontos": "7.000 - 10.499 pontos",
        "min_pontos": 7000,
        "imagem": "tarefas/ranks/diamante.png",
        "desc": "Grandes conquistas!",
        "obtivel": True,
    },
    {
        "slug": "cosmico",
        "nome": "Cósmico",
        "faixa_pontos": "10.500 - 12.999 pontos",
        "min_pontos": 10500,
        "imagem": "tarefas/ranks/cosmico.png",
        "desc": "De outro nível!",
        "obtivel": True,
    },
    {
        "slug": "estelar",
        "nome": "Estelar",
        "faixa_pontos": "13.000 - 14.999 pontos",
        "min_pontos": 13000,
        "imagem": "tarefas/ranks/estelar.png",
        "desc": "Brilhe ainda mais!",
        "obtivel": True,
    },
    {
        "slug": "galactos",
        "nome": "Galáctus",
        "faixa_pontos": "15.000+ pontos",
        "min_pontos": 15000,
        "imagem": "tarefas/ranks/galactos.png",
        "desc": "O auge da produtividade!",
        "obtivel": True,
    },
]

RANK_ADMIN = {
    "slug": "admin",
    "nome": "Admin",
    "faixa_pontos": "Não é um rank obtível",
    "min_pontos": None,
    "imagem": "tarefas/ranks/admin.png",
    "desc": "Rank exclusivo para AkiiraPW, Guster260, Hollow e usuários presenteados.",
    "obtivel": False,
}

RANKS_TRILHA = list(RANKS_OBTIVEIS)
RANKS_TABELA = [
    RANK_ADMIN,
    *reversed(RANKS_OBTIVEIS),
]

CONTAS_ADMIN_NATIVAS = {"akiirapw", "guster260", "hollow"}


def usuario_tem_acesso_admin(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    username_low = (user.username or "").strip().lower()
    if username_low in CONTAS_ADMIN_NATIVAS:
        return True
    try:
        presente = RankPresente.objects.filter(usuario=user, rank_slug="admin").first()
        return presente is not None
    except Exception:
        return False


def obter_rank_por_slug(slug: str):
    if not slug:
        return None
    slug_low = slug.strip().lower()
    if slug_low == "admin":
        return RANK_ADMIN
    for r in RANKS_OBTIVEIS:
        if r["slug"] == slug_low:
            return r
    return None


def calcular_ranking_por_pontos(pontos: int, user=None) -> dict:
    pontos = max(0, int(pontos or 0))
    atual = RANKS_OBTIVEIS[0]
    proximo = None

    for idx, rank in enumerate(RANKS_OBTIVEIS):
        if pontos >= rank["min_pontos"]:
            atual = rank
            proximo = RANKS_OBTIVEIS[idx + 1] if idx + 1 < len(RANKS_OBTIVEIS) else None

    if proximo is None:
        progresso_pct = 100
        pontos_faltando = 0
    else:
        span = max(1, proximo["min_pontos"] - atual["min_pontos"])
        progresso_pct = min(100, max(0, int(((pontos - atual["min_pontos"]) / span) * 100)))
        pontos_faltando = max(0, proximo["min_pontos"] - pontos)

    rank_exibido = atual
    presenteado = False

    if user is not None and getattr(user, "is_authenticated", False):
        try:
            registro = RankPresente.objects.filter(usuario=user).order_by("-id").first()
            if registro:
                rank_gift = obter_rank_por_slug(registro.rank_slug)
                if rank_gift:
                    rank_exibido = rank_gift
                    presenteado = True
        except Exception:
            pass

        if (user.username or "").strip().lower() in CONTAS_ADMIN_NATIVAS and rank_exibido["slug"] != "admin":
            rank_exibido = RANK_ADMIN
            presenteado = True

    return {
        "pontos": pontos,
        "rank_slug": rank_exibido["slug"],
        "rank_nome": rank_exibido["nome"],
        "rank_imagem": rank_exibido["imagem"],
        "rank_desc": rank_exibido["desc"],
        "rank_obtivel": rank_exibido["obtivel"],
        "rank_presenteado": presenteado,
        "rank_min": atual["min_pontos"],
        "proximo_rank": proximo["nome"] if proximo else "Galáctus",
        "proximo_imagem": proximo["imagem"] if proximo else "tarefas/ranks/galactos.png",
        "proximo_pontos": proximo["min_pontos"] if proximo else atual["min_pontos"],
        "pontos_faltando": pontos_faltando,
        "progresso_pct": progresso_pct,
        "todos_ranks": RANKS_TABELA,
        "ranks_trilha": RANKS_TRILHA,
        "rank_admin_info": RANK_ADMIN,
        "ranks_obtiveis": list(reversed(RANKS_OBTIVEIS)),
    }


def avaliar_conquistas(concluidas_count: int, dias_ativos_count: int, tempo_segundos: int) -> list:
    horas = tempo_segundos / 3600.0
    return [
        {
            "icone": "👑",
            "nome": "Primeiros Passos",
            "desc": "1 dia ativo no site",
            "desbloqueada": dias_ativos_count >= 1,
            "progresso": f"{min(dias_ativos_count, 1)}/1 dia",
        },
        {
            "icone": "🛡️",
            "nome": "Sempre Presente",
            "desc": "7 dias logado",
            "desbloqueada": dias_ativos_count >= 7,
            "progresso": f"{min(dias_ativos_count, 7)}/7 dias",
        },
        {
            "icone": "⏱️",
            "nome": "Foco Total",
            "desc": "2h de atividade no site",
            "desbloqueada": tempo_segundos >= 7200,
            "progresso": f"{min(horas, 2.0):.1f}/2.0h",
        },
        {
            "icone": "💎",
            "nome": "Produtivo",
            "desc": "50 tarefas concluídas",
            "desbloqueada": concluidas_count >= 50,
            "progresso": f"{min(concluidas_count, 50)}/50 tarefas",
        },
    ]


class RankPresente(models.Model):
    RANK_CHOICES = [
        ("admin", "Admin (Não obtível)"),
        ("galactos", "Galáctus"),
        ("estelar", "Estelar"),
        ("cosmico", "Cósmico"),
        ("diamante", "Diamante"),
        ("platina", "Platina"),
        ("ouro", "Ouro"),
        ("prata", "Prata"),
        ("bronze", "Bronze"),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="rank_presente")
    rank_slug = models.CharField(max_length=30, choices=RANK_CHOICES, default="admin")
    concedido_por = models.CharField(max_length=150, default="AkiiraPW")
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.usuario.username} -> {self.rank_slug}"


class Materia(models.Model):
    nome = models.CharField(max_length=100)
    professor = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class Tarefa(models.Model):
    TIPO_CHOICES = [
        ('Tarefa', 'Tarefa'),
        ('Trabalho', 'Trabalho'),
        ('Prova', 'Prova'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('média', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    titulo = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    data = models.DateField()
    horario = models.TimeField()
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES
    )
    concluida = models.BooleanField(default=False)

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='Tarefa'
    )

    materia = models.ForeignKey(
        Materia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.titulo


class HorarioAula(models.Model):
    DIA_CHOICES = [
        ('Segunda', 'Segunda-feira'),
        ('Terça', 'Terça-feira'),
        ('Quarta', 'Quarta-feira'),
        ('Quinta', 'Quinta-feira'),
        ('Sexta', 'Sexta-feira'),
    ]

    dia_semana = models.CharField(
        max_length=20,
        choices=DIA_CHOICES
    )

    horario_inicio = models.TimeField()

    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.dia_semana} - {self.materia.nome}"


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto_perfil = models.ImageField(upload_to='perfis/', blank=True, null=True)
    imagem_fundo = models.FileField(upload_to='fundos/', blank=True, null=True)
    bio = models.CharField(max_length=160, blank=True, default="Sonhe. Planeje. Conquiste.")
    sobre = models.TextField(blank=True, default="Olá! Estou organizando minha rotina escolar e buscando evoluir todos os dias. ✨")
    tempo_ativo_segundos = models.PositiveIntegerField(default=0)
    dias_logados = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"