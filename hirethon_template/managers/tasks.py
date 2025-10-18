import logging
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
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


@celery_app.task(bind=True, max_retries=2)
def create_slots_daily_task(self):
    """
    Daily task to create and manage slots for the next 7 days
    """
    logger.info("Starting daily slot creation task")
    
    try:
        from .slot_service import SlotScheduler
        
        scheduler = SlotScheduler()
        
        # Create slots for the next 7 days
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        
        logger.info(f"Creating slots from {today} to {end_date}")
        
        result = scheduler.create_slots_for_period(today, end_date)
        
        if result.get('success', False):
            logger.info(f"Successfully created {result.get('total_slots_created', 0)} slots")
        else:
            logger.error(f"Slot creation failed: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as exc:
        logger.error(f"Daily slot creation task failed: {str(exc)}", exc_info=True)
        
        # Retry once more if it's the first attempt
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying slot creation task in 5 minutes")
            raise self.retry(countdown=300, exc=exc)
        else:
            logger.error(f"Slot creation task permanently failed after {self.max_retries} retries")
            raise exc


@celery_app.task(bind=True)
def revalidate_slot_assignments_task(self, team_id=None, days_back=1):
    """
    Task to revalidate existing slot assignments and fix constraint violations
    Can be triggered manually or after swaps
    """
    logger.info(f"Starting slot validation task for team {team_id or 'all'}")
    
    try:
        from .slot_service import SlotScheduler
        from .models import Team
        
        scheduler = SlotScheduler()
        
        # Calculate start date
        start_date = timezone.now().date() - timedelta(days=days_back)
        
        team = None
        if team_id:
            try:
                team = Team.objects.get(id=team_id, is_active=True)
            except Team.DoesNotExist:
                logger.error(f"Team {team_id} not found or inactive")
                return {"success": False, "error": "Team not found"}
        
        result = scheduler.revalidate_assignments(team=team, start_date=start_date)
        
        if result.get('success', False):
            logger.info(f"Validation complete: {result.get('violations_found', 0)} violations found, "
                       f"{result.get('violations_fixed', 0)} fixed")
        else:
            logger.error(f"Validation failed: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as exc:
        logger.error(f"Slot validation task failed: {str(exc)}", exc_info=True)
        raise exc


@celery_app.task(bind=True)
def cleanup_old_slots_task(self, days_to_keep=30):
    """
    Task to cleanup old slots that are no longer needed
    """
    logger.info(f"Starting cleanup of slots older than {days_to_keep} days")
    
    try:
        from .models import Slot
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Find old completed slots
        old_slots = Slot.objects.filter(
            end_time__lt=cutoff_date,
            assigned_member__isnull=True  # Only cleanup unassigned old slots
        )
        
        count = old_slots.count()
        old_slots.delete()
        
        logger.info(f"Cleaned up {count} old unassigned slots")
        
        return {
            "success": True,
            "slots_deleted": count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Slot cleanup task failed: {str(exc)}", exc_info=True)
        raise exc
