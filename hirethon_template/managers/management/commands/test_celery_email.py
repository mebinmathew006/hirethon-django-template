from django.core.management.base import BaseCommand
from hirethon_template.managers.tasks import send_user_credentials_email_task


class Command(BaseCommand):
    help = 'Test Celery email task'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to send test email to')
        parser.add_argument('--name', type=str, default='Test User', help='Name for the test email')

    def handle(self, *args, **options):
        email = options.get('email')
        name = options.get('name', 'Test User')
        
        if not email:
            self.stdout.write(
                self.style.ERROR('Please provide an email address using --email')
            )
            return
        
        self.stdout.write(f'Queueing Celery email task for {email}...')
        
        try:
            # Call the task directly (synchronously) for testing
            result = send_user_credentials_email_task.apply(
                kwargs={
                    'user_email': email,
                    'user_name': name,
                    'password': 'test_password_123',
                    'is_manager': False
                }
            )
            
            if result.successful():
                self.stdout.write(
                    self.style.SUCCESS(f'Celery email task completed successfully: {result.result}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Celery email task failed: {result.result}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running Celery email task: {str(e)}')
            )
