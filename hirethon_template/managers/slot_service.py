"""
Slot creation and management service for fair scheduling with constraints
"""
import logging
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Team, TeamMember, Slot, Availability, Holiday

logger = logging.getLogger(__name__)
User = get_user_model()


class SlotScheduler:
    """
    Service class for creating and managing on-call slots with constraints
    """
    
    def __init__(self):
        self.logger = logger
    
    def create_slots_for_period(self, start_date: date, end_date: date, team: Team = None) -> Dict:
        """
        Create slots for all teams or a specific team for the given period
        
        Args:
            start_date: Start date for slot creation
            end_date: End date for slot creation  
            team: Optional specific team, if None creates for all active teams
            
        Returns:
            Dict with creation results
        """
        try:
            if team:
                teams = [team] if team.is_active else []
            else:
                teams = Team.objects.filter(is_active=True)
            
            if not teams:
                self.logger.warning("No active teams found for slot creation")
                return {"success": False, "message": "No active teams found"}
            
            total_slots_created = 0
            results = []
            
            with transaction.atomic():
                for team in teams:
                    team_result = self._create_team_slots(team, start_date, end_date)
                    results.append(team_result)
                    total_slots_created += team_result.get('slots_created', 0)
            
            self.logger.info(f"Created {total_slots_created} slots for {len(teams)} teams")
            return {
                "success": True,
                "total_slots_created": total_slots_created,
                "teams_processed": len(teams),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Error creating slots: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _create_team_slots(self, team: Team, start_date: date, end_date: date) -> Dict:
        """
        Create slots for a specific team within the date range
        """
        try:
            # Get active team members
            active_members = TeamMember.objects.filter(
                team=team, 
                is_active=True,
                user__is_active=True
            ).select_related('user')
            
            if not active_members.exists():
                return {
                    "team_id": team.id,
                    "team_name": team.name,
                    "success": False,
                    "message": "No active members found"
                }
            
            # Convert duration to hours for calculations
            slot_duration_hours = team.slot_duration.total_seconds() / 3600
            
            # Create slots for each day in the period
            current_date = start_date
            slots_created = 0
            
            while current_date <= end_date:
                # Skip if it's a team holiday
                if Holiday.objects.filter(team=team, date=current_date).exists():
                    current_date += timedelta(days=1)
                    continue
                
                # Calculate number of slots needed for this day (24 hours)
                slots_per_day = int(24 / slot_duration_hours)
                
                for slot_number in range(slots_per_day):
                    start_time = timezone.make_aware(datetime.combine(
                        current_date, 
                        time(hour=int(slot_number * slot_duration_hours))
                    ))
                    end_time = start_time + team.slot_duration
                    
                    # Check if slot already exists
                    if Slot.objects.filter(team=team, start_time=start_time).exists():
                        continue
                    
                    # Create the slot (unassigned initially)
                    slot = Slot.objects.create(
                        team=team,
                        start_time=start_time,
                        end_time=end_time,
                        is_holiday=False,
                        is_covered=False
                    )
                    slots_created += 1
                
                current_date += timedelta(days=1)
            
            # Now assign slots fairly
            assignment_result = self._assign_slots_fairly(team, start_date, end_date)
            
            return {
                "team_id": team.id,
                "team_name": team.name,
                "success": True,
                "slots_created": slots_created,
                "assignment_result": assignment_result
            }
            
        except Exception as e:
            self.logger.error(f"Error creating slots for team {team.id}: {str(e)}", exc_info=True)
            return {
                "team_id": team.id,
                "team_name": team.name,
                "success": False,
                "error": str(e)
            }
    
    def _assign_slots_fairly(self, team: Team, start_date: date, end_date: date) -> Dict:
        """
        Assign slots to team members with constraints and fair rotation
        """
        try:
            # Get active team members
            members = list(TeamMember.objects.filter(
                team=team, is_active=True, user__is_active=True
            ).select_related('user'))
            
            if not members:
                return {"success": False, "message": "No active members"}
            
            # Get unassigned slots for this team and period
            unassigned_slots = Slot.objects.filter(
                team=team,
                start_time__date__range=[start_date, end_date],
                assigned_member__isnull=True
            ).order_by('start_time')
            
            assignments_made = 0
            violations = []
            
            # Create a set of valid team member user IDs for quick lookup
            valid_team_member_ids = {member.user.id for member in members if member.user and member.user.is_active}
            
            for slot in unassigned_slots:
                assigned_member = self._find_best_member_for_slot(slot, members)
                
                if assigned_member:
                    # CRITICAL SAFETY CHECK: Ensure assigned member is actually a team member
                    if assigned_member.id not in valid_team_member_ids:
                        violations.append({
                            "slot_id": slot.id,
                            "member_id": assigned_member.id,
                            "violation": f"User {assigned_member.name} is not a member of team {team.name}"
                        })
                        continue
                    
                    # Validate constraints before assignment
                    violation = self._validate_assignment_constraints(slot, assigned_member)
                    if not violation:
                        slot.assigned_member = assigned_member
                        slot.is_covered = True
                        slot.save()
                        assignments_made += 1
                    else:
                        violations.append({
                            "slot_id": slot.id,
                            "member_id": assigned_member.id,
                            "violation": violation
                        })
                else:
                    violations.append({
                        "slot_id": slot.id,
                        "member_id": None,
                        "violation": "No suitable member found"
                    })
            
            return {
                "success": True,
                "assignments_made": assignments_made,
                "total_slots": unassigned_slots.count(),
                "violations": violations
            }
            
        except Exception as e:
            self.logger.error(f"Error assigning slots for team {team.id}: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _find_best_member_for_slot(self, slot: Slot, members: List[TeamMember]) -> Optional[User]:
        """
        Find the best member to assign to a slot based on constraints and fairness
        """
        slot_date = slot.start_time.date()
        slot_hours = slot.duration.total_seconds() / 3600
        
        # Validate that we only consider actual team members
        team_users = set()
        valid_members = []
        
        for member in members:
            # Ensure this is actually a team member
            if hasattr(member, 'user') and member.user and member.user.is_active:
                team_users.add(member.user.id)
                valid_members.append(member)
        
        if not valid_members:
            return None
        
        # Get member scores (lower is better)
        member_scores = []
        
        for member in valid_members:
            user = member.user
            
            # Double-check user is a team member (safety check)
            if user.id not in team_users:
                continue
                
            score = 0
            
            # Check availability (penalty for unavailable)
            if not self._is_user_available(user, slot_date):
                continue  # Skip unavailable users
            
            # Check daily hours constraint (including this slot if assigned) - using team constraints
            daily_hours = self._get_user_daily_hours(user, slot_date)
            if daily_hours + slot_hours > slot.team.max_hours_per_day:
                continue  # Skip if would exceed daily limit
            
            # Check weekly hours constraint - using team constraints
            week_start = slot_date - timedelta(days=slot_date.weekday())
            weekly_hours = self._get_user_weekly_hours(user, week_start)
            if weekly_hours + slot_hours > slot.team.max_hours_per_week:
                continue  # Skip if would exceed weekly limit
            
            # Check rest hours constraint - CRITICAL FIX for consecutive slots - using team constraints
            if not self._has_sufficient_rest(user, slot.start_time, slot.team.min_rest_hours):
                continue  # Skip if insufficient rest
            
            # FIXED: Check for consecutive slots on the same day
            if self._has_consecutive_slot_on_date(user, slot):
                continue  # Skip if would create consecutive slots on same day
            
            # Calculate fairness score (lower recent assignments = lower score)
            recent_assignments = self._get_recent_assignments(user, slot_date)
            score += recent_assignments * 3  # Increased weight for fairness
            
            # Check total assignments for rotation
            total_assignments = Slot.objects.filter(
                assigned_member=user,
                start_time__date__gte=slot_date - timedelta(days=30)  # Last 30 days
            ).count()
            score += total_assignments * 0.5  # Increased penalty for more assignments
            
            member_scores.append((user, score))
        
        if not member_scores:
            return None
        
        # Sort by score and return the best candidate
        member_scores.sort(key=lambda x: x[1])
        return member_scores[0][0]
    
    def _is_user_available(self, user: User, check_date: date) -> bool:
        """Check if user is available on a given date"""
        try:
            availability = Availability.objects.get(user=user, date=check_date)
            return availability.is_available
        except Availability.DoesNotExist:
            return True  # Available by default
    
    def _get_user_daily_hours(self, user: User, check_date: date) -> float:
        """Get total assigned hours for user on a specific date"""
        start_of_day = datetime.combine(check_date, time.min)
        end_of_day = datetime.combine(check_date, time.max)
        
        slots = Slot.objects.filter(
            assigned_member=user,
            start_time__gte=start_of_day,
            start_time__lte=end_of_day
        )
        
        total_hours = sum(
            slot.duration.total_seconds() / 3600 for slot in slots
        )
        return total_hours
    
    def _get_user_weekly_hours(self, user: User, week_start: date) -> float:
        """Get total assigned hours for user in a week"""
        start_of_week = datetime.combine(week_start, time.min)
        end_of_week = start_of_week + timedelta(days=7)
        
        slots = Slot.objects.filter(
            assigned_member=user,
            start_time__gte=start_of_week,
            start_time__lt=end_of_week
        )
        
        total_hours = sum(
            slot.duration.total_seconds() / 3600 for slot in slots
        )
        return total_hours
    
    def _has_sufficient_rest(self, user: User, slot_start: datetime, min_rest_hours: float) -> bool:
        """Check if user has sufficient rest before the slot"""
        min_rest_time = timedelta(hours=min_rest_hours)
        
        # Check for slots that end close to this slot's start time
        slot_end_before = slot_start - timedelta(hours=1)  # Check 1 hour before
        slot_start_after = slot_start + timedelta(hours=1)  # Check 1 hour after
        
        conflicting_slots = Slot.objects.filter(
            assigned_member=user,
            start_time__lte=slot_start_after,
            end_time__gte=slot_end_before
        ).exclude(id=getattr(self, '_current_slot_id', None))  # Exclude current slot being checked
        
        if conflicting_slots.exists():
            return False  # User already has a slot that conflicts
        
        # Check for sufficient rest from the last slot
        last_slot_end = Slot.objects.filter(
            assigned_member=user,
            end_time__lt=slot_start,
            end_time__gte=slot_start - timedelta(days=2)  # Check last 2 days
        ).order_by('-end_time').first()
        
        if not last_slot_end:
            return True  # No previous slot
        
        rest_period = slot_start - last_slot_end.end_time
        return rest_period >= min_rest_time
    
    def _has_consecutive_slot_on_date(self, user: User, slot: Slot) -> bool:
        """Check if user already has a slot that is consecutive to this one on the same date"""
        from django.utils import timezone
        
        slot_date = slot.start_time.date()
        
        # Get all slots for this user on this date (excluding the current slot being assigned)
        start_of_day = timezone.make_aware(datetime.combine(slot_date, time.min))
        end_of_day = timezone.make_aware(datetime.combine(slot_date, time.max))
        
        existing_slots = Slot.objects.filter(
            assigned_member=user,
            start_time__gte=start_of_day,
            start_time__lte=end_of_day,
            team=slot.team  # Ensure same team
        ).exclude(id=slot.id).order_by('start_time')  # Exclude the slot being assigned
        
        if not existing_slots.exists():
            return False  # No existing slots on this date
        
        slot_start = slot.start_time
        slot_end = slot.end_time
        
        # Check if this slot would be consecutive with any existing slot
        for existing_slot in existing_slots:
            # Check if slots are consecutive (start of new slot = end of existing, or vice versa)
            if (existing_slot.end_time == slot_start or 
                slot_end == existing_slot.start_time):
                return True
        
        return False
    
    def _get_recent_assignments(self, user: User, reference_date: date) -> int:
        """Get number of recent assignments (for fairness)"""
        # Count assignments in the last 7 days
        week_start = reference_date - timedelta(days=7)
        
        return Slot.objects.filter(
            assigned_member=user,
            start_time__date__gte=week_start,
            start_time__date__lt=reference_date
        ).count()
    
    def _validate_assignment_constraints(self, slot: Slot, user: User) -> Optional[str]:
        """
        Validate all constraints for a slot assignment
        Returns violation message if constraints are violated, None if valid
        """
        slot_date = slot.start_time.date()
        slot_hours = slot.duration.total_seconds() / 3600
        
        # Availability check
        if not self._is_user_available(user, slot_date):
            return "User is not available on this date"
        
        # Daily hours check - using team constraints
        daily_hours = self._get_user_daily_hours(user, slot_date)
        if daily_hours + slot_hours > slot.team.max_hours_per_day:
            return f"Would exceed daily limit ({slot.team.max_hours_per_day}h)"
        
        # Weekly hours check - using team constraints
        week_start = slot_date - timedelta(days=slot_date.weekday())
        weekly_hours = self._get_user_weekly_hours(user, week_start)
        if weekly_hours + slot_hours > slot.team.max_hours_per_week:
            return f"Would exceed weekly limit ({slot.team.max_hours_per_week}h)"
        
        # Rest hours check - using team constraints
        if not self._has_sufficient_rest(user, slot.start_time, slot.team.min_rest_hours):
            return f"Insufficient rest time (minimum {slot.team.min_rest_hours}h required)"
        
        return None  # No violations
    
    def revalidate_assignments(self, team: Team = None, start_date: date = None) -> Dict:
        """
        Revalidate existing slot assignments and fix constraint violations
        Useful after swaps or schedule changes
        """
        try:
            if not start_date:
                start_date = timezone.now().date()
            
            # Get slots to revalidate
            slots_query = Slot.objects.filter(
                start_time__date__gte=start_date,
                assigned_member__isnull=False
            )
            
            if team:
                slots_query = slots_query.filter(team=team)
            
            violations_found = 0
            violations_fixed = 0
            
            for slot in slots_query.select_related('assigned_member', 'team'):
                violation = self._validate_assignment_constraints(slot, slot.assigned_member)
                
                if violation:
                    violations_found += 1
                    self.logger.warning(
                        f"Constraint violation in slot {slot.id}: {violation}"
                    )
                    
                    # Try to find a better assignment
                    team_members = TeamMember.objects.filter(
                        team=slot.team,
                        is_active=True,
                        user__is_active=True
                    ).select_related('user')
                    
                    new_member = self._find_best_member_for_slot(slot, list(team_members))
                    
                    if new_member and new_member != slot.assigned_member:
                        slot.assigned_member = new_member
                        slot.save()
                        violations_fixed += 1
                        self.logger.info(f"Fixed slot {slot.id} assignment")
            
            return {
                "success": True,
                "violations_found": violations_found,
                "violations_fixed": violations_fixed
            }
            
        except Exception as e:
            self.logger.error(f"Error revalidating assignments: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
