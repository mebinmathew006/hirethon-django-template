# Generated manually to handle SwapRequest model changes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0005_add_leave_request_model'),
    ]

    operations = [
        # First, delete all existing swap requests to avoid conflicts
        migrations.RunSQL(
            sql="DELETE FROM managers_swaprequest;",
            reverse_sql="-- No reverse operation needed",
        ),
        
        # Remove old fields
        migrations.RemoveField(
            model_name='swaprequest',
            name='slot',
        ),
        migrations.RemoveField(
            model_name='swaprequest',
            name='from_member',
        ),
        migrations.RemoveField(
            model_name='swaprequest',
            name='to_member',
        ),
        
        # Add new fields
        migrations.AddField(
            model_name='swaprequest',
            name='from_slot',
            field=models.ForeignKey(help_text='The slot the user wants to swap FROM', on_delete=django.db.models.deletion.CASCADE, related_name='swap_requests_from', to='managers.slot'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='swaprequest',
            name='to_slot',
            field=models.ForeignKey(help_text='The slot the user wants to swap TO', on_delete=django.db.models.deletion.CASCADE, related_name='swap_requests_to', to='managers.slot'),
            preserve_default=False,
        ),
        
        # Add the unique constraint
        migrations.AlterUniqueTogether(
            name='swaprequest',
            unique_together={('from_slot', 'to_slot', 'created_at')},
        ),
    ]
