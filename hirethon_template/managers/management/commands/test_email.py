from django.core.management.base import BaseCommand
from hirethon_template.utils.email import send_user_credentials_email


class Command(BaseCommand):
    help = 'Test email sending functionality'

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
        
        self.stdout.write(f'Sending test email to {email}...')
        
        success = send_user_credentials_email(
            user_email=email,
            user_name=name,
            password='test_password_123',
            is_manager=False
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'Test email sent successfully to {email}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'Failed to send test email to {email}')
            )
