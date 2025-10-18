from django.contrib.auth import get_user_model
from config import celery_app

from hirethon_template.utils.email import send_user_credentials_email

User = get_user_model()


@celery_app.task(bind=True, max_retries=3)
def send_user_credentials_email_task(self, user_email, user_name, password, is_manager=False):
    """
    Celery task to send user credentials via email
    """
    try:
        success = send_user_credentials_email(
            user_email=user_email,
            user_name=user_name,
            password=password,
            is_manager=is_manager
        )
        
        if not success:
            # Retry the task if email sending fails
            raise Exception("Failed to send email")
            
        return f"Email sent successfully to {user_email}"
        
    except Exception as exc:
        # Log the error and retry
        print(f"Email task failed for {user_email}: {str(exc)}")
        
        # Retry up to max_retries times
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # Exponential backoff
            raise self.retry(countdown=countdown, exc=exc)
        else:
            # If all retries failed, log the failure
            print(f"Email task permanently failed for {user_email} after {self.max_retries} retries")
            raise exc
