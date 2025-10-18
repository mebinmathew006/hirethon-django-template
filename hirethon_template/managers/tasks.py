import logging
from django.contrib.auth import get_user_model
from config import celery_app

logger = logging.getLogger(__name__)

User = get_user_model()


@celery_app.task(bind=True, max_retries=3)
def send_user_credentials_email_task(self, user_email, user_name, password, is_manager=False):
    """
    Celery task to send user credentials via email
    """
    logger.info(f"Starting email task for user: {user_email}")
    
    try:
        # Import here to avoid circular imports
        from hirethon_template.utils.email import send_user_credentials_email
        
        logger.info(f"Attempting to send email to {user_email}")
        success = send_user_credentials_email(
            user_email=user_email,
            user_name=user_name,
            password=password,
            is_manager=is_manager
        )
        
        if not success:
            logger.error(f"Email sending failed for {user_email}")
            raise Exception("Failed to send email")
            
        logger.info(f"Email sent successfully to {user_email}")
        return f"Email sent successfully to {user_email}"
        
    except Exception as exc:
        logger.error(f"Email task failed for {user_email}: {str(exc)}", exc_info=True)
        
        # Retry up to max_retries times
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # Exponential backoff
            logger.info(f"Retrying email task for {user_email} in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=exc)
        else:
            # If all retries failed, log the failure
            logger.error(f"Email task permanently failed for {user_email} after {self.max_retries} retries")
            raise exc
