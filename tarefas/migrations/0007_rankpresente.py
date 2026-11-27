from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tarefas', '0006_perfil_bio_perfil_sobre'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RankPresente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank_slug', models.CharField(choices=[('admin', 'Admin (Não obtível)'), ('galactos', 'Galáctus'), ('estelar', 'Estelar'), ('cosmico', 'Cósmico'), ('diamante', 'Diamante'), ('platina', 'Platina'), ('ouro', 'Ouro'), ('prata', 'Prata'), ('bronze', 'Bronze')], default='admin', max_length=30)),
                ('concedido_por', models.CharField(default='AkiiraPW', max_length=150)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank_presente', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]