from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tarefas", "0008_perfil_imagem_fundo_filefield"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfil",
            name="tempo_ativo_segundos",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="perfil",
            name="dias_logados",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
