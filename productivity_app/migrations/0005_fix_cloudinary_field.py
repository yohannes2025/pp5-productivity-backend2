# productivity_app/migrations/0005_fix_cloudinary_field.py
from django.db import migrations
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        # <-- change only if your last migration number is different
        ('productivity_app', '__first__'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file',
            field=cloudinary.models.CloudinaryField(
                max_length=255,
                verbose_name='file',
                folder='task_files'
            ),
        ),
    ]
