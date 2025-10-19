from django.apps import AppConfig


class ManagersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hirethon_template.managers'

    def ready(self):
        """Set up periodic tasks when the app is ready"""
        # Import models to ensure signals are registered
        from . import models  # This will import the signals defined in models.py
        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
            from .tasks import create_slots_daily_task, check_empty_slots_notification_task
            
            # Create daily slot creation task (runs at 2 AM every day)
            daily_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=2,
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            
            if created:
                print("Created crontab schedule for daily slot creation")
            
            # Create the daily periodic task if it doesn't exist
            daily_task, task_created = PeriodicTask.objects.get_or_create(
                name='Daily Slot Creation',
                defaults={
                    'crontab': daily_schedule,
                    'task': 'hirethon_template.managers.tasks.create_slots_daily_task',
                    'enabled': True,
                    'description': 'Daily task to create and assign slots for the next 7 days',
                }
            )
            
            if task_created:
                print("Created daily slot creation periodic task")
            
            # Create minute-based empty slots check task (runs every minute)
            minute_schedule, created = IntervalSchedule.objects.get_or_create(
                every=1,
                period=IntervalSchedule.MINUTES,
            )
            
            if created:
                print("Created interval schedule for minute-based empty slots check")
            
            # Create or update the notification task
            notification_task, notif_created = PeriodicTask.objects.get_or_create(
                name='Empty Slots Notification Check',
                defaults={
                    'interval': minute_schedule,
                    'task': 'hirethon_template.managers.tasks.check_empty_slots_notification_task',
                    'enabled': True,
                    'description': 'Task to check for empty slots in next 72 hours and create notifications (every minute)',
                }
            )
            
            # Update existing task to use new schedule
            if not notif_created and notification_task.interval != minute_schedule:
                notification_task.interval = minute_schedule
                notification_task.description = 'Task to check for empty slots in next 72 hours and create notifications (every minute)'
                notification_task.save()
                print("Updated existing notification task to run every minute")
            
            if notif_created:
                print("Created minute-based notification periodic task")
            
        except Exception as e:
            # Don't let app startup fail if celery beat tables don't exist yet
            print(f"Could not set up periodic tasks: {e}")