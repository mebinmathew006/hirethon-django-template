from django.core.management.base import BaseCommand
from django.db import transaction
from hirethon_template.managers.models import Team, TeamMember, Slot, Alert, Holiday, Availability, LeaveRequest, SwapRequest


class Command(BaseCommand):
    help = 'Remove all teams and team members from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion (required for safety)'
        )
        parser.add_argument(
            '--keep-superuser',
            action='store_true',
            help='Keep superuser data intact (recommended)'
        )

    def handle(self, *args, **options):
        confirm = options.get('confirm')
        keep_superuser = options.get('keep_superuser', True)

        if not confirm:
            self.stdout.write(
                self.style.ERROR('❌ This will delete ALL teams and team members!')
            )
            self.stdout.write(
                '⚠️  WARNING: This action cannot be undone!'
            )
            self.stdout.write('Use --confirm flag to proceed.')
            return

        self.stdout.write('🗑️  Starting cleanup of teams and team members...')

        try:
            with transaction.atomic():
                # Get counts before deletion
                team_count = Team.objects.count()
                team_member_count = TeamMember.objects.count()
                slot_count = Slot.objects.count()
                alert_count = Alert.objects.count()
                holiday_count = Holiday.objects.count()
                availability_count = Availability.objects.count()
                leave_request_count = LeaveRequest.objects.count()
                swap_request_count = SwapRequest.objects.count()

                self.stdout.write(f'📊 Current data counts:')
                self.stdout.write(f'  Teams: {team_count}')
                self.stdout.write(f'  Team Members: {team_member_count}')
                self.stdout.write(f'  Slots: {slot_count}')
                self.stdout.write(f'  Alerts: {alert_count}')
                self.stdout.write(f'  Holidays: {holiday_count}')
                self.stdout.write(f'  Availabilities: {availability_count}')
                self.stdout.write(f'  Leave Requests: {leave_request_count}')
                self.stdout.write(f'  Swap Requests: {swap_request_count}')

                if team_count == 0:
                    self.stdout.write(
                        self.style.WARNING('ℹ️  No teams found. Nothing to delete.')
                    )
                    return

                self.stdout.write('\n🗑️  Deleting related data...')

                # Delete in proper order due to foreign key constraints
                # 1. Delete swap requests (references slots)
                deleted_swap_requests = SwapRequest.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_swap_requests[0]} swap requests')

                # 2. Delete alerts (references slots)
                deleted_alerts = Alert.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_alerts[0]} alerts')

                # 3. Delete slots (references teams)
                deleted_slots = Slot.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_slots[0]} slots')

                # 4. Delete leave requests (references teams and users)
                deleted_leave_requests = LeaveRequest.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_leave_requests[0]} leave requests')

                # 5. Delete availability records (references users)
                deleted_availabilities = Availability.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_availabilities[0]} availability records')

                # 6. Delete holidays (references teams)
                deleted_holidays = Holiday.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_holidays[0]} holidays')

                # 7. Delete team members (references teams and users)
                deleted_team_members = TeamMember.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_team_members[0]} team members')

                # 8. Finally, delete teams
                deleted_teams = Team.objects.all().delete()
                self.stdout.write(f'  ✅ Deleted {deleted_teams[0]} teams')

                # Verify deletion
                remaining_teams = Team.objects.count()
                remaining_team_members = TeamMember.objects.count()
                remaining_slots = Slot.objects.count()
                remaining_alerts = Alert.objects.count()

                self.stdout.write('\n📈 Cleanup Summary:')
                self.stdout.write(f'  Teams: {team_count} → {remaining_teams}')
                self.stdout.write(f'  Team Members: {team_member_count} → {remaining_team_members}')
                self.stdout.write(f'  Slots: {slot_count} → {remaining_slots}')
                self.stdout.write(f'  Alerts: {alert_count} → {remaining_alerts}')

                if remaining_teams == 0 and remaining_team_members == 0:
                    self.stdout.write(
                        self.style.SUCCESS('\n🎉 Successfully removed all teams and team members!')
                    )
                    self.stdout.write('✅ Database is now clean of team-related data.')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'\n❌ Some data still remains: {remaining_teams} teams, {remaining_team_members} team members')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during cleanup: {str(e)}')
            )
            raise
