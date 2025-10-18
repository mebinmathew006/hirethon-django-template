import logging
from django.core.mail import send_mail
from django.conf import settings
import os

logger = logging.getLogger(__name__)


def send_user_credentials_email(user_email, user_name, password, is_manager=False):
    """
    Send an email with user credentials to the newly created user
    """
    logger.info(f"Attempting to send credentials email to {user_email}")
    
    subject = 'Welcome! Your Account Has Been Created'
    
    role = "Manager" if is_manager else "User"
    
    message = f"""Dear {user_name},

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
    
    # Use DEFAULT_FROM_EMAIL from settings
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'care@spicelush.com')
    
    logger.info(f"Email configuration: FROM={from_email}, TO={user_email}, BACKEND={getattr(settings, 'EMAIL_BACKEND', 'default')}")
    
    try:
        # Check current email backend configuration
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
        email_host = getattr(settings, 'EMAIL_HOST', None)
        email_user = getattr(settings, 'EMAIL_HOST_USER', None)
        
        logger.info(f"Current email settings: BACKEND={email_backend}, HOST={email_host}, USER={email_user}")
        
        # Send the email using Django's configured email backend
        result = send_mail(
            subject,
            message,
            from_email,
            [user_email],
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {user_email}, result: {result}")
        return True
            
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {str(e)}", exc_info=True)
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
