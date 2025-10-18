from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from hirethon_template.managers.models import Slot, Team, TeamMember
from hirethon_template.managers.tasks import check_empty_slots_notification_function

User = get_user_model()

class Command(BaseCommand):
    help = 'Test the 1-hour notification task by creating/deleting slots and running the task'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['run', 'create-empty-slot', 'delete-slot', 'check-notifications', 'show-slots'],
            default='run',
            help='Action to perform: run task, create empty slot, delete slot, check notifications, or show slots'
        )
        parser.add_argument(
            '--slot-id',
            type=int,
            help='Slot ID for delete action'
        )
        parser.add_argument(
            '--team-id',
            type=int,
            help='Team ID for creating empty slot'
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'run':
            self.run_notification_task()
        elif action == 'create-empty-slot':
            self.create_empty_slot(options.get('team_id'))
        elif action == 'delete-slot':
            slot_id = options.get('slot_id')
            if not slot_id:
                self.stdout.write(
                    self.style.ERROR('--slot-id is required for delete-slot action')
                )
                return
            self.delete_slot(slot_id)
        elif action == 'check-notifications':
            self.check_notifications()
        elif action == 'show-slots':
            self.show_slots()

    def run_notification_task(self):
        """Run the notification task manually"""
        self.stdout.write('Running the 1-hour notification task...')
        
        try:
            # Call the function directly (not through Celery)
            result = check_empty_slots_notification_function()
            
            self.stdout.write(
                self.style.SUCCESS(f'Task completed successfully!')
            )
            self.stdout.write(f'Result: {result}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Task failed: {str(e)}')
            )

    def create_empty_slot(self, team_id):
        """Create an empty slot within the next 72 hours for testing"""
        if not team_id:
            # Get the first active team
            team = Team.objects.filter(is_active=True).first()
            if not team:
                self.stdout.write(
                    self.style.ERROR('No active teams found. Please create a team first.')
                )
                return
            team_id = team.id
        else:
            try:
                team = Team.objects.get(id=team_id, is_active=True)
            except Team.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Team with ID {team_id} not found or not active.')
                )
                return

        # Create a slot in the next 24-48 hours (within 72 hour window)
        now = timezone.now()
        start_time = now + timedelta(hours=25)  # 25 hours from now
        
        # Create an 8-hour slot (assuming default slot duration)
        slot = Slot.objects.create(
            team=team,
            start_time=start_time,
            end_time=start_time + timedelta(hours=8),
            assigned_member=None  # This makes it empty
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created empty slot ID {slot.id} for team "{team.name}" '
                f'starting at {start_time.isoformat()}'
            )
        )

    def delete_slot(self, slot_id):
        """Delete a specific slot to create an empty slot scenario"""
        try:
            slot = Slot.objects.get(id=slot_id)
            team_name = slot.team.name if slot.team else 'Unknown'
            start_time = slot.start_time
            assigned_member = slot.assigned_member.name if slot.assigned_member else 'None'
            
            slot.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Deleted slot ID {slot_id} from team "{team_name}" '
                    f'starting at {start_time.isoformat()} (was assigned to: {assigned_member})'
                )
            )
            
        except Slot.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Slot with ID {slot_id} not found.')
            )

    def check_notifications(self):
        """Check current notifications in cache"""
        from django.core.cache import cache
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        notifications = cache.get("empty_slots_notifications", [])
        
        # Filter out old notifications (same logic as API view)
        cutoff_time = timezone.now() - timedelta(hours=24)
        recent_notifications = []
        
        for notification in notifications:
            try:
                notification_time = datetime.fromisoformat(
                    notification.get('notification_time', '').replace('Z', '+00:00')
                )
                if timezone.is_naive(notification_time):
                    notification_time = timezone.make_aware(notification_time)
                
                if notification_time >= cutoff_time:
                    recent_notifications.append(notification)
            except (ValueError, TypeError):
                # Skip invalid timestamps
                continue
        
        if notifications:
            self.stdout.write(
                self.style.SUCCESS(f'Found {len(notifications)} total notifications, {len(recent_notifications)} recent:')
            )
            for i, notification in enumerate(recent_notifications, 1):
                self.stdout.write(
                    f'  {i}. Slot ID {notification.get("slot_id")} - '
                    f'Team: {notification.get("team_name")} - '
                    f'Starts: {notification.get("start_time")} - '
                    f'Hours from now: {notification.get("hours_from_now")}'
                )
        else:
            self.stdout.write(
                self.style.WARNING('No notifications found in cache.')
            )

    def show_slots(self):
        """Show all slots in the next 72 hours"""
        now = timezone.now()
        end_time = now + timedelta(hours=72)
        
        slots = Slot.objects.filter(
            start_time__gte=now,
            start_time__lte=end_time
        ).select_related('team', 'assigned_member').order_by('start_time')
        
        if slots.exists():
            self.stdout.write(
                self.style.SUCCESS(f'Found {slots.count()} slots in next 72 hours:')
            )
            self.stdout.write('=' * 80)
            
            for slot in slots:
                assigned_to = slot.assigned_member.name if slot.assigned_member else 'EMPTY ⚠️'
                hours_from_now = round((slot.start_time - now).total_seconds() / 3600, 1)
                
                status = self.style.SUCCESS if slot.assigned_member else self.style.ERROR
                
                self.stdout.write(f'ID: {slot.id} | Team: {slot.team.name}')
                self.stdout.write(f'  Start: {slot.start_time.strftime("%Y-%m-%d %H:%M")}')
                self.stdout.write(f'  End: {slot.end_time.strftime("%Y-%m-%d %H:%M")}')
                self.stdout.write(f'  Assigned to: {assigned_to}')
                self.stdout.write(f'  Hours from now: {hours_from_now}h')
                self.stdout.write('-' * 80)
        else:
            self.stdout.write(
                self.style.WARNING('No slots found in next 72 hours.')
            )

    def show_help(self):
        """Show usage examples"""
        self.stdout.write('\nUsage examples:')
        self.stdout.write('  python manage.py test_notification_task run')
        self.stdout.write('  python manage.py test_notification_task create-empty-slot --team-id 1')
        self.stdout.write('  python manage.py test_notification_task delete-slot --slot-id 123')
        self.stdout.write('  python manage.py test_notification_task check-notifications')
        self.stdout.write('  python manage.py test_notification_task show-slots')
