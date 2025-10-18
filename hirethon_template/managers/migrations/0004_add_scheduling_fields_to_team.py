# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0003_update_availability_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='max_hours_per_day',
            field=models.FloatField(default=8),
        ),
        migrations.AddField(
            model_name='team',
            name='max_hours_per_week',
            field=models.FloatField(default=40),
        ),
        migrations.AddField(
            model_name='team',
            name='min_rest_hours',
            field=models.FloatField(default=8),
        ),
    ]
