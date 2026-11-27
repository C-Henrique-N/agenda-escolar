from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tarefas", "0007_rankpresente"),
    ]

    operations = [
        migrations.AlterField(
            model_name="perfil",
            name="imagem_fundo",
            field=models.FileField(blank=True, null=True, upload_to="fundos/"),
        ),
    ]
