from django.apps import AppConfig


class ManagersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hirethon_template.managers'

    def ready(self):
        """Set up periodic tasks when the app is ready"""
        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
            from .tasks import create_slots_daily_task
            
            # Create daily slot creation task (runs at 2 AM every day)
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=2,
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            if created:
                print("Created crontab schedule for daily slot creation")
            
            # Create the periodic task if it doesn't exist
            task, task_created = PeriodicTask.objects.get_or_create(
                name='Daily Slot Creation',
                defaults={
                    'crontab': schedule,
                    'task': 'hirethon_template.managers.tasks.create_slots_daily_task',
                    'enabled': True,
                    'description': 'Daily task to create and assign slots for the next 7 days',
                }
            )
            
            if task_created:
                print("Created daily slot creation periodic task")
            
        except Exception as e:
            # Don't let app startup fail if celery beat tables don't exist yet
            print(f"Could not set up periodic tasks: {e}")