# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='max_hours_per_day',
        ),
        migrations.RemoveField(
            model_name='user',
            name='max_hours_per_week',
        ),
        migrations.RemoveField(
            model_name='user',
            name='min_rest_hours',
        ),
    ]
