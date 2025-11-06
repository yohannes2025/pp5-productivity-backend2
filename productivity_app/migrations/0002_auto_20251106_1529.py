from django.db import migrations, models
from django.contrib.auth import get_user_model


def assign_first_user_to_profiles(apps, schema_editor):
    Profile = apps.get_model('productivity_app', 'Profile')
    User = get_user_model()
    first_user = User.objects.first()
    if first_user:
        Profile.objects.filter(user__isnull=True).update(user=first_user)


class Migration(migrations.Migration):
    dependencies = [
        ('productivity_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                related_name='profile',
                to='auth.user',
            ),
        ),
        migrations.RunPython(assign_first_user_to_profiles),
    ]