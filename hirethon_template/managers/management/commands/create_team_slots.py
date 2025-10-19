from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from hirethon_template.managers.models import Team
from hirethon_template.managers.slot_service import SlotScheduler


class Command(BaseCommand):
    help = 'Manually create slots for a team that was recently activated'

    def add_arguments(self, parser):
        parser.add_argument(
            '--team-id',
            type=int,
            help='Team ID to create slots for (if not provided, will show all teams)'
        )
        parser.add_argument(
            '--team-name',
            type=str,
            help='Team name to create slots for (alternative to team-id)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force slot creation even if team is inactive'
        )

    def handle(self, *args, **options):
        team_id = options.get('team_id')
        team_name = options.get('team_name')
        force = options.get('force', False)

        # Find the team
        if team_id:
            try:
                team = Team.objects.get(id=team_id)
            except Team.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Team with ID {team_id} not found.')
                )
                return
        elif team_name:
            try:
                team = Team.objects.get(name=team_name)
            except Team.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Team with name "{team_name}" not found.')
                )
                return
        else:
            # Show all teams and let user choose
            self.show_all_teams()
            return

        # Check if team is active
        if not team.is_active and not force:
            self.stdout.write(
                self.style.ERROR(
                    f'Team "{team.name}" is not active. Use --force to create slots anyway.'
                )
            )
            return

        # Get team info
        min_required = team.calculate_minimum_members()
        active_members = team.get_active_member_count()
        
        self.stdout.write(f'Team: {team.name}')
        self.stdout.write(f'Active: {team.is_active}')
        self.stdout.write(f'Active members: {active_members}/{min_required} (minimum required: {min_required})')

        if not force and active_members < min_required:
            self.stdout.write(
                self.style.WARNING(
                    f'Team does not have enough members ({active_members}/{min_required}). Use --force to create slots anyway.'
                )
            )
            return

        # Create slots
        self.stdout.write('Creating slots...')
        
        scheduler = SlotScheduler()
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        
        self.stdout.write(f'Creating slots from {today} to {end_date}')
        
        try:
            result = scheduler.create_slots_for_period(today, end_date, team=team)
            
            if result.get('success', False):
                slots_created = result.get('total_slots_created', 0)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully created {slots_created} slots for team "{team.name}"'
                    )
                )
                
                # Show detailed results
                results = result.get('results', [])
                for team_result in results:
                    if team_result.get('success', False):
                        assignments = team_result.get('assignment_result', {})
                        assignments_made = assignments.get('assignments_made', 0)
                        total_slots = assignments.get('total_slots', 0)
                        
                        self.stdout.write(f'  Slots created: {team_result.get("slots_created", 0)}')
                        self.stdout.write(f'  Assignments made: {assignments_made}/{total_slots}')
                        
                        violations = assignments.get('violations', [])
                        if violations:
                            self.stdout.write(f'  Constraint violations: {len(violations)}')
                            for violation in violations[:3]:  # Show first 3
                                self.stdout.write(f'    - {violation.get("violation", "Unknown")}')
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  Failed: {team_result.get("error", "Unknown error")}')
                        )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create slots: {result.get("error", "Unknown error")}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating slots: {str(e)}')
            )

    def show_all_teams(self):
        """Show all teams with their status"""
        teams = Team.objects.all().order_by('name')
        
        if not teams.exists():
            self.stdout.write(self.style.WARNING('No teams found.'))
            return
            
        self.stdout.write('\nAvailable teams:')
        self.stdout.write('=' * 80)
        
        for team in teams:
            min_required = team.calculate_minimum_members()
            active_members = team.get_active_member_count()
            status = 'Active' if team.is_active else 'Inactive'
            
            self.stdout.write(f'ID: {team.id:3d} | {team.name:20s} | {status:8s} | Members: {active_members:2d}/{min_required}')
        
        self.stdout.write('\nUse --team-id or --team-name to specify which team to create slots for.')
