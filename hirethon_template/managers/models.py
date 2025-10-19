from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import timedelta

User = get_user_model()
# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=255)
    slot_duration = models.DurationField(default=timedelta(hours=1))
    max_hours_per_day = models.FloatField(default=8)
    max_hours_per_week = models.FloatField(default=40)
    min_rest_hours = models.FloatField(default=8)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    def calculate_minimum_members(self):
        """
        Calculate the minimum number of members needed based on:
        - max_hours_per_day: maximum hours one member can work per day
        - max_hours_per_week: maximum hours one member can work per week
        - min_rest_hours: minimum rest hours between shifts for one member
        - slot_duration: duration of each slot
        """
        # Convert slot duration to hours
        slot_duration_hours = self.slot_duration.total_seconds() / 3600
        
        # Calculate how many slots one member can handle per day considering rest hours
        # Minimum time between shifts should include the slot duration + rest hours
        min_time_between_slots = slot_duration_hours + self.min_rest_hours
        
        # Calculate maximum slots one member can handle per day
        # Assuming 24 hours available, minus rest periods
        max_slots_per_day_per_member = 24 / min_time_between_slots if min_time_between_slots > 0 else 1
        
        # But also limit by max_hours_per_day
        max_slots_per_day_by_hours = self.max_hours_per_day / slot_duration_hours if slot_duration_hours > 0 else 1
        max_slots_per_day_per_member = min(max_slots_per_day_per_member, max_slots_per_day_by_hours)
        
        # For continuous coverage (24/7), we need to calculate how many members
        # are needed to cover all slots throughout the day
        total_slots_per_day = 24 / slot_duration_hours if slot_duration_hours > 0 else 24
        
        # Calculate minimum members needed for daily coverage
        min_members_for_daily = max(1, int(total_slots_per_day / max_slots_per_day_per_member) + 1)
        
        # Also consider weekly limits
        max_slots_per_week_per_member = (self.max_hours_per_week / slot_duration_hours) if slot_duration_hours > 0 else 40
        total_slots_per_week = total_slots_per_day * 7
        min_members_for_weekly = max(1, int(total_slots_per_week / max_slots_per_week_per_member) + 1)
        
        # Return the higher of the two calculations
        return max(min_members_for_daily, min_members_for_weekly)
    
    def get_active_member_count(self):
        """Get the number of active members in this team"""
        return self.members.filter(is_active=True).count()
    
    def update_active_status(self):
        """
        Update the team's is_active status based on whether it has enough members
        When a team becomes active, trigger slot creation for the next 7 days
        """
        from django.utils import timezone
        from datetime import timedelta
        
        min_required = self.calculate_minimum_members()
        active_count = self.get_active_member_count()
        
        should_be_active = active_count >= min_required
        was_inactive = not self.is_active
        was_active = self.is_active
        
        if self.is_active != should_be_active:
            self.is_active = should_be_active
            self.save(update_fields=['is_active'])
            
            # If team just became active, trigger slot creation
            if was_inactive and should_be_active:
                try:
                    from .slot_service import SlotScheduler
                    
                    # Create slots for the next 7 days for this team
                    today = timezone.now().date()
                    end_date = today + timedelta(days=7)
                    
                    scheduler = SlotScheduler()
                    result = scheduler.create_slots_for_period(today, end_date, team=self)
                    
                    # Log the slot creation result
                    import logging
                    logger = logging.getLogger(__name__)
                    if result.get('success', False):
                        slots_created = result.get('total_slots_created', 0)
                        # Check if assignments were successful by looking at results
                        results = result.get('results', [])
                        assignment_success = False
                        if results:
                            assignment_result = results[0].get('assignment_result', {})
                            assignment_success = assignment_result.get('success', False)
                        
                        assignment_info = "and assigned to members" if assignment_success else ""
                        logger.info(f"✅ Team '{self.name}' became active and triggered slot creation: {slots_created} slots created {assignment_info}")
                    else:
                        logger.warning(f"⚠️  Failed to create slots for newly active team '{self.name}': {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"❌ Error triggering slot creation for newly active team '{self.name}': {str(e)}", exc_info=True)
            
            # Also log when team becomes inactive
            elif was_active and not should_be_active:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"⚠️  Team '{self.name}' became inactive (has {active_count} members, needs {min_required})")
            
            return True  # Status was changed
        
        return False  # Status was already correct
    
    def reassign_slots_from_next_day(self):
        """
        Comprehensive slot recalculation when new members are added to an active team
        Uses the new recalculate_slots_for_new_member method that properly considers leave requests
        """
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.is_active:
            return False
            
        try:
            from .slot_service import SlotScheduler
            
            # Start from tomorrow to avoid disrupting current day's assignments
            tomorrow = timezone.now().date() + timedelta(days=1)
            end_date = tomorrow + timedelta(days=6)  # Next 7 days from tomorrow
            
            scheduler = SlotScheduler()
            
            # Use the comprehensive recalculation method that considers leave requests
            result = scheduler.recalculate_slots_for_new_member(self, tomorrow, end_date)
            
            # Log the recalculation result with enhanced details
            import logging
            logger = logging.getLogger(__name__)
            if result.get('success', False):
                slots_reassigned = result.get('slots_reassigned', 0)
                slots_created = result.get('slots_created', 0)
                new_assignments = result.get('new_assignments', 0)
                members_count = result.get('members_count', 0)
                leave_summary = result.get('leave_summary', {})
                total_slots = result.get('total_slots', 0)
                
                log_parts = []
                if slots_created > 0:
                    log_parts.append(f"created {slots_created} new slots")
                if slots_reassigned > 0:
                    log_parts.append(f"reassigned {slots_reassigned} existing slots")
                if new_assignments > 0:
                    log_parts.append(f"made {new_assignments} new assignments")
                
                action_summary = ", ".join(log_parts) if log_parts else "processed slots"
                logger.info(f"🔄 {action_summary} from {tomorrow} for team '{self.name}' ({members_count} members, {total_slots} total slots) after new member addition")
                
                if leave_summary:
                    logger.info(f"🏖️ Leave requests considered: {leave_summary}")
                
                logger.info(f"✅ New member integrated successfully into rotation")
            else:
                logger.warning(f"⚠️  Failed to recalculate slots for team '{self.name}': {result.get('error', 'Unknown error')}")
                
            return result.get('success', False)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error recalculating slots for team '{self.name}': {str(e)}", exc_info=True)
            return False
    
    @property
    def minimum_required_members(self):
        """Property to get minimum required members"""
        return self.calculate_minimum_members()

class TeamMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    is_manager = models.BooleanField(default=False)  # optional per team
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'team')

class Holiday(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="holidays")
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ('team', 'date')

class Availability(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="availability")
    date = models.DateField()  # The date when the user has leave/unavailability record
    is_available = models.BooleanField(default=True)  # True = available, False = unavailable (leave/PTO)
    reason = models.CharField(max_length=255, blank=True, help_text="Reason for unavailability (e.g., 'PTO', 'Sick leave')")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'date')
        verbose_name_plural = 'availabilities'
    
    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.user.name} - {self.date} ({status})"


class Slot(models.Model):
    """
    Represents an on-call shift/slot for a team
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="slots")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    assigned_member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_slots')
    is_holiday = models.BooleanField(default=False)
    is_covered = models.BooleanField(default=False, help_text="True if the slot is covered by an assigned member")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('team', 'start_time')
        ordering = ['start_time']
    
    def __str__(self):
        if self.assigned_member:
            return f"{self.team.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')} ({self.assigned_member.name})"
        return f"{self.team.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')} (Unassigned)"
    
    @property
    def date(self):
        """Get the date of this slot"""
        return self.start_time.date()
    
    @property
    def duration(self):
        """Get the duration of this slot"""
        return self.end_time - self.start_time
    
    def is_active_now(self):
        """Check if this slot is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class SwapRequest(models.Model):
    from_slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='swap_requests_from', help_text="The slot the user wants to swap FROM")
    to_slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='swap_requests_to', help_text="The slot the user wants to swap TO")
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('from_slot', 'to_slot', 'created_at')
    
    def is_pending(self):
        return not (self.accepted or self.rejected)
    
    @property
    def from_member(self):
        """Get the member who wants to swap (from_slot's assigned member)"""
        return self.from_slot.assigned_member if self.from_slot else None
    
    @property
    def to_member(self):
        """Get the member who would receive the swap (to_slot's assigned member)"""
        return self.to_slot.assigned_member if self.to_slot else None

        
class Alert(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='alerts')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='leave_requests')
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leave_requests')
    
    class Meta:
        unique_together = ('user', 'team', 'date')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.date} ({self.status})"


# Signals to automatically update team active status when members are added/removed/modified
@receiver(post_save, sender=TeamMember)
def update_team_status_on_member_change(sender, instance, **kwargs):
    """
    Update team active status whenever a team member is saved (created or updated)
    Also reassign slots from next day when a new member is added to an active team
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔄 TeamMember signal triggered - Team: {instance.team.name if instance.team else 'None'}, Is Active: {instance.is_active}, Created: {kwargs.get('created', False)}")
        
        if instance.team and instance.is_active:
            logger.info(f"📊 Updating team status for team '{instance.team.name}' - Current active: {instance.team.is_active}")
            
            # Update team status first
            team_status_changed = instance.team.update_active_status()
            
            logger.info(f"📈 Team status update result - Changed: {team_status_changed}, Team now active: {instance.team.is_active}")
            
            # If team was already active and team status didn't change, 
            # this means a member was added/reactivated to an already active team
            # So we need to reassign slots to include the new member
            if instance.team.is_active and not team_status_changed:
                # Check if this was a new member creation (the serializer handles reactivation case)
                is_new_member = kwargs.get('created', False)
                logger.info(f"🔍 Checking slot reassignment - Is new member: {is_new_member}")
                
                if is_new_member:
                    logger.info(f"🔧 Triggering slot reassignment for team '{instance.team.name}' due to new member addition")
                    instance.team.reassign_slots_from_next_day()
                else:
                    logger.info(f"⏭️ Skipping slot reassignment - not a new member creation")
            else:
                logger.info(f"⏭️ Skipping slot reassignment - Team active: {instance.team.is_active}, Status changed: {team_status_changed}")
        else:
            logger.info(f"⏭️ Signal skipped - No team or member not active. Team: {instance.team is not None}, Member active: {instance.is_active}")
            
    except Exception as e:
        logger.error(f"❌ Error in TeamMember signal: {str(e)}", exc_info=True)


@receiver(post_delete, sender=TeamMember)
def update_team_status_on_member_delete(sender, instance, **kwargs):
    """
    Update team active status whenever a team member is deleted
    Also reassign slots from next day when a member is removed from an active team
    """
    if instance.team:
        # Update team status first
        team_status_changed = instance.team.update_active_status()
        
        # If team remains active after member deletion, reassign slots from tomorrow
        if instance.team.is_active and not team_status_changed:
            instance.team.reassign_slots_from_next_day()
