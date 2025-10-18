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


def check_empty_slots_notification_function():
    """
    Standalone function to check for empty slots within next 72 hours and send notifications
    This can be called directly without Celery
    """
    logger.info("Starting empty slots check function")
    
    try:
        from datetime import datetime, timedelta
        from django.utils import timezone
        from .models import Slot, Team, Alert
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Calculate time window (next 72 hours)
        now = timezone.now()
        end_time = now + timedelta(hours=72)
        
        # Find empty slots within the next 72 hours
        empty_slots = Slot.objects.filter(
            start_time__gte=now,
            start_time__lte=end_time,
            assigned_member__isnull=True
        ).select_related('team').order_by('start_time')
        
        if empty_slots.exists():
            # Get all managers to notify
            managers = User.objects.filter(is_manager=True, is_active=True)
            
            # Group slots by team and time
            notifications = []
            for slot in empty_slots:
                slot_data = {
                    'slot_id': slot.id,
                    'team_id': slot.team.id,
                    'team_name': slot.team.name,
                    'start_time': slot.start_time.isoformat(),
                    'end_time': slot.end_time.isoformat(),
                    'hours_from_now': round((slot.start_time - now).total_seconds() / 3600, 1)
                }
                notifications.append(slot_data)
            
            # Update the notification status in cache/database
            # For now, we'll store in cache - later this can be WebSocket
            from django.core.cache import cache
            
            notification_key = "empty_slots_notifications"
            existing_notifications = cache.get(notification_key, [])
            
            # Add new notifications (avoid duplicates)
            for notification in notifications:
                if not any(n['slot_id'] == notification['slot_id'] for n in existing_notifications):
                    existing_notifications.append({
                        **notification,
                        'notification_time': now.isoformat(),
                        'type': 'empty_slot'
                    })
            
            # Store in cache for 24 hours
            cache.set(notification_key, existing_notifications, 86400)
            
            # Create Alert records for each empty slot (avoid duplicates)
            alerts_created = 0
            new_alerts = []
            for slot in empty_slots:
                # Check if alert already exists for this slot (not resolved)
                existing_alert = Alert.objects.filter(
                    slot=slot,
                    resolved=False
                ).first()
                
                if not existing_alert:
                    message = f"Empty slot detected: {slot.team.name} on {slot.start_time.strftime('%Y-%m-%d %H:%M')} - {slot.end_time.strftime('%Y-%m-%d %H:%M')} ({round((slot.start_time - now).total_seconds() / 3600, 1)} hours from now)"
                    
                    alert = Alert.objects.create(
                        team=slot.team,
                        slot=slot,
                        message=message
                    )
                    alerts_created += 1
                    new_alerts.append(alert)
            
            logger.info(f"Found {empty_slots.count()} empty slots in next 72 hours, created {alerts_created} new alerts")
            
            # Send WebSocket notifications for new alerts
            if new_alerts:
                send_websocket_notifications.delay([alert.id for alert in new_alerts])
            
            return {
                "success": True,
                "empty_slots_count": empty_slots.count(),
                "notifications_created": len(notifications),
                "alerts_created": alerts_created,
                "time_window": {
                    "from": now.isoformat(),
                    "to": end_time.isoformat()
                }
            }
        else:
            logger.info("No empty slots found in next 72 hours")
            return {
                "success": True,
                "empty_slots_count": 0,
                "message": "No empty slots found"
            }
            
    except Exception as exc:
        logger.error(f"Empty slots check function failed: {str(exc)}", exc_info=True)
        raise exc


@celery_app.task(bind=True)
def check_empty_slots_notification_task(self):
    """
    Celery task wrapper for the notification check function
    """
    return check_empty_slots_notification_function()


@celery_app.task
def send_websocket_notifications(alert_ids):
    """
    Send WebSocket notifications for new alerts
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from .models import Alert
        
        # Get the alerts
        alerts = Alert.objects.filter(id__in=alert_ids).select_related('slot', 'team')
        
        channel_layer = get_channel_layer()
        if channel_layer:
            for alert in alerts:
                hours_from_now = round((alert.slot.start_time - timezone.now()).total_seconds() / 3600, 1)
                
                notification_data = {
                    'slot_id': alert.slot.id,
                    'team_id': alert.team.id,
                    'team_name': alert.team.name,
                    'start_time': alert.slot.start_time.isoformat(),
                    'end_time': alert.slot.end_time.isoformat(),
                    'notification_time': alert.created_at.isoformat(),
                    'type': 'empty_slot_alert',
                    'alert_id': alert.id,
                    'message': alert.message,
                    'hours_from_now': hours_from_now,
                    'is_empty': True,
                    'assigned_user': None
                }
                
                async_to_sync(channel_layer.group_send)(
                    'admin_notifications',
                    {
                        'type': 'send_alert',
                        'data': notification_data,
                        'timestamp': alert.created_at.isoformat()
                    }
                )
            
            logger.info(f"Sent WebSocket notifications for {len(alerts)} new alerts")
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket notifications: {str(e)}", exc_info=True)
