from django.db import models
from django.contrib.auth.models import User


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


# ==========================================
# ADICIONE ESTE MODEL NO FINAL DO SEU models.py
# ==========================================
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto_perfil = models.ImageField(upload_to='perfis/', blank=True, null=True)
    imagem_fundo = models.ImageField(upload_to='fundos/', blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"