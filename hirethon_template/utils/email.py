from django.core.mail import send_mail
from django.conf import settings
import os


def send_user_credentials_email(user_email, user_name, password, is_manager=False):
    """
    Send an email with user credentials to the newly created user
    """
    subject = 'Welcome! Your Account Has Been Created'
    
    role = "Manager" if is_manager else "User"
    
    message = f"""
Dear {user_name},

Welcome to our platform! Your account has been successfully created.

Account Details:
- Email: {user_email}
- Password: {password}
- Role: {role}

For security reasons, we recommend you change your password after your first login.

To login, please visit our platform and use the credentials above.

If you have any questions or need assistance, please don't hesitate to contact us.

Best regards,
The Team
"""
    
    # Use DEFAULT_FROM_EMAIL from settings, fallback to care@spicelush.com
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'care@spicelush.com')
    
    # Check if SMTP configuration is available from environment variables
    smtp_host = os.getenv('EMAIL_HOST')
    smtp_user = os.getenv('EMAIL_HOST_USER')
    smtp_password = os.getenv('EMAIL_HOST_PASSWORD')
    
    # Fallback to hardcoded values if environment variables are not available
    if not smtp_host:
        smtp_host = 'smtp.gmail.com'
    if not smtp_user:
        smtp_user = 'mebinmathew006@gmail.com'
    if not smtp_password:
        smtp_password = 'qopm tqga anur yotk'
    
    try:
        # Use SMTP configuration (either from env vars or fallback values)
        if smtp_host and smtp_user and smtp_password:
            # Temporarily set SMTP configuration
            original_backend = settings.EMAIL_BACKEND
            original_host = getattr(settings, 'EMAIL_HOST', None)
            original_port = getattr(settings, 'EMAIL_PORT', None)
            original_use_tls = getattr(settings, 'EMAIL_USE_TLS', None)
            original_host_user = getattr(settings, 'EMAIL_HOST_USER', None)
            original_host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            
            settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            settings.EMAIL_HOST = smtp_host
            settings.EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
            settings.EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
            settings.EMAIL_HOST_USER = smtp_user
            settings.EMAIL_HOST_PASSWORD = smtp_password
            
            try:
                result = send_mail(
                    subject,
                    message,
                    from_email,
                    [user_email],
                    fail_silently=False,
                )
                return True
            finally:
                # Restore original settings
                settings.EMAIL_BACKEND = original_backend
                if original_host is not None:
                    settings.EMAIL_HOST = original_host
                if original_port is not None:
                    settings.EMAIL_PORT = original_port
                if original_use_tls is not None:
                    settings.EMAIL_USE_TLS = original_use_tls
                if original_host_user is not None:
                    settings.EMAIL_HOST_USER = original_host_user
                if original_host_password is not None:
                    settings.EMAIL_HOST_PASSWORD = original_host_password
        else:
            # Use default Django mail configuration
            send_mail(
                subject,
                message,
                from_email,
                [user_email],
                fail_silently=False,
            )
            return True
            
    except Exception as e:
        # Log the error (in production, you might want to use Django's logging here)
        print(f"Failed to send email to {user_email}: {str(e)}")
        return False


def send_user_welcome_email(user_email, user_name, login_url=None):
    """
    Send a welcome email after successful registration (alternative approach)
    """
    subject = 'Welcome to Our Platform!'
    
    message = f"""
Dear {user_name},

Welcome to our platform! We're excited to have you on board.

{f'You can access your account here: {login_url}' if login_url else ''}

If you have any questions or need assistance, please don't hesitate to contact us.

Best regards,
The Team
"""
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'care@spicelush.com')
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            [user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send welcome email to {user_email}: {str(e)}")
        return False
