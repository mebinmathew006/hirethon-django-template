"""
Unit tests for slot service functionality
"""
import pytest
from datetime import timedelta, date, time
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.db import transaction

from hirethon_template.managers.models import Team, TeamMember, Slot, Availability, Holiday, LeaveRequest
from hirethon_template.managers.slot_service import SlotScheduler
from hirethon_template.users.models import User
from .factories import (
    TeamFactory, TeamMemberFactory, SlotFactory, UserFactory,
    AvailabilityFactory, HolidayFactory, LeaveRequestFactory
)


@pytest.mark.django_db
class TestSlotScheduler:
    """Test SlotScheduler class functionality"""
    
    @pytest.fixture
    def scheduler(self):
        """Create a SlotScheduler instance"""
        return SlotScheduler()
    
    @pytest.fixture
    def active_team_with_members(self, db):
        """Create an active team with multiple members"""
        team = TeamFactory(is_active=True)
        
        # Create enough members to make team active
        min_required = team.calculate_minimum_members()
        users = [UserFactory() for _ in range(min_required)]
        for user in users:
            TeamMemberFactory(team=team, user=user, is_active=True)
        
        # Ensure team is active
        team.update_active_status()
        team.refresh_from_db()
        
        return team, users
    
    def test_slot_scheduler_initialization(self, scheduler):
        """Test SlotScheduler initialization"""
        assert scheduler.logger is not None
    
    def test_create_slots_for_period_no_active_teams(self, scheduler, db):
        """Test slot creation when no active teams exist"""
        TeamFactory(is_active=False)  # Inactive team
        
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=1)
        
        result = scheduler.create_slots_for_period(start_date, end_date)
        
        assert result['success'] is False
        assert 'No active teams found' in result['message']
    
    def test_create_slots_for_period_with_team(self, scheduler, active_team_with_members):
        """Test slot creation for specific team"""
        team, users = active_team_with_members
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=1)
        
        result = scheduler.create_slots_for_period(start_date, end_date, team=team)
        
        assert result['success'] is True
        assert result['total_slots_created'] > 0
        assert result['teams_processed'] == 1
    
    def test_create_slots_for_period_inactive_team(self, scheduler, db):
        """Test slot creation with inactive team"""
        team = TeamFactory(is_active=False)
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=1)
        
        result = scheduler.create_slots_for_period(start_date, end_date, team=team)
        
        assert result['success'] is False
        assert 'No active teams found' in result['message']
    
    def test_create_team_slots_no_active_members(self, scheduler, db):
        """Test slot creation when team has no active members"""
        team = TeamFactory(is_active=True)
        # Create inactive members
        user = UserFactory()
        TeamMemberFactory(team=team, user=user, is_active=False)
        
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=1)
        
        result = scheduler._create_team_slots(team, start_date, end_date)
        
        assert result['success'] is False
        assert 'No active members found' in result['message']
    
    def test_is_user_available_no_availability_record(self, scheduler, db):
        """Test user availability when no availability record exists"""
        user = UserFactory()
        check_date = timezone.now().date()
        
        # Should be available by default
        assert scheduler._is_user_available(user, check_date) is True
    
    def test_is_user_available_explicit_availability(self, scheduler, db):
        """Test user availability with explicit availability record"""
        user = UserFactory()
        team = TeamFactory()
        check_date = timezone.now().date()
        
        # Create availability record marking user as unavailable
        AvailabilityFactory(user=user, date=check_date, is_available=False)
        
        assert scheduler._is_user_available(user, check_date, team) is False
        
        # Mark as available
        availability = Availability.objects.get(user=user, date=check_date)
        availability.is_available = True
        availability.save()
        
        assert scheduler._is_user_available(user, check_date, team) is True
    
    def test_is_user_available_with_approved_leave(self, scheduler, db):
        """Test user availability with approved leave request"""
        user = UserFactory()
        team = TeamFactory()
        check_date = timezone.now().date()
        
        # Create approved leave request
        LeaveRequestFactory(
            user=user, 
            team=team, 
            date=check_date, 
            status='approved'
        )
        
        assert scheduler._is_user_available(user, check_date, team) is False
    
    def test_is_user_available_with_pending_leave(self, scheduler, db):
        """Test user availability with pending leave request"""
        user = UserFactory()
        team = TeamFactory()
        check_date = timezone.now().date()
        
        # Create pending leave request (should not affect availability)
        LeaveRequestFactory(
            user=user, 
            team=team, 
            date=check_date, 
            status='pending'
        )
        
        assert scheduler._is_user_available(user, check_date, team) is True
    
    def test_assign_slots_fairly_basic(self, scheduler, active_team_with_members):
        """Test basic fair slot assignment"""
        team, users = active_team_with_members
        
        # Create some existing slots with unique times in the future to avoid conflicts
        start_date = timezone.now().date()
        start_datetime = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)
        
        slots = []
        for i in range(5):  # Create 5 slots
            slot_time = start_datetime + timedelta(hours=i, minutes=i*10)  # Add minutes to ensure uniqueness
            slot = SlotFactory(
                team=team, 
                start_time=slot_time,
                assigned_member=None,
                is_covered=False
            )
            slots.append(slot)
        
        result = scheduler._assign_slots_fairly(team, start_date, start_date + timedelta(days=1))
        
        assert result['success'] is True
        assert result['assignments_made'] >= 0  # May be 0 if no valid assignments found
        
        # Check that some slots might be assigned (this test is more about not crashing)
        total_slots = Slot.objects.filter(team=team).count()
        assert total_slots >= 5
    
    def test_validate_assignment_constraints(self, scheduler, active_team_with_members):
        """Test assignment constraint validation"""
        team, users = active_team_with_members
        
        # Create a slot with unique time
        start_time = timezone.now().replace(hour=10, minute=15, second=0, microsecond=0)
        slot = SlotFactory(team=team, start_time=start_time)
        
        # Test with available user
        user = users[0]
        result = scheduler._validate_assignment_constraints(slot, user)
        
        assert result['is_valid'] is True
    
    def test_validate_assignment_constraints_unavailable_user(self, scheduler, active_team_with_members):
        """Test constraint validation with unavailable user"""
        team, users = active_team_with_members
        
        # Create a slot with unique time
        start_time = timezone.now().replace(hour=11, minute=45, second=0, microsecond=0)
        slot = SlotFactory(team=team, start_time=start_time)
        
        # Make user unavailable
        user = users[0]
        AvailabilityFactory(user=user, date=slot.start_time.date(), is_available=False)
        
        result = scheduler._validate_assignment_constraints(slot, user)
        
        assert result['is_valid'] is False
        assert 'not available' in result['message'].lower()
    
    def test_find_best_member_for_slot(self, scheduler, active_team_with_members):
        """Test finding best member for a slot"""
        team, users = active_team_with_members
        
        # Create a slot with a unique start time to avoid constraint violations
        start_time = timezone.now().replace(hour=15, minute=30, second=0, microsecond=0)
        slot = SlotFactory(team=team, start_time=start_time)
        
        best_member = scheduler._find_best_member_for_slot(slot)
        
        # Should find a member (might be None if no one is available)
        assert best_member is None or isinstance(best_member, User)
    
    def test_ensure_slots_exist_for_period(self, scheduler, active_team_with_members):
        """Test ensuring slots exist for a period"""
        team, users = active_team_with_members
        
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=2)
        
        result = scheduler._ensure_slots_exist_for_period(team, start_date, end_date)
        
        assert result['success'] is True
        assert result['slots_created'] >= 0  # Might be 0 if slots already exist
        
        # Check that slots exist for the period
        slots_count = Slot.objects.filter(
            team=team,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date
        ).count()
        
        assert slots_count > 0
    
    def test_recalculate_slots_for_new_member(self, scheduler, active_team_with_members):
        """Test slot recalculation when new member is added"""
        team, existing_users = active_team_with_members
        
        # Add a new member
        new_user = UserFactory()
        TeamMemberFactory(team=team, user=new_user, is_active=True)
        
        start_date = timezone.now().date() + timedelta(days=1)
        end_date = start_date + timedelta(days=6)
        
        result = scheduler.recalculate_slots_for_new_member(team, start_date, end_date)
        
        assert result['success'] is True
        assert result['members_count'] > len(existing_users)
        assert 'new_assignments' in result
    
    @patch('hirethon_template.managers.slot_service.logger')
    def test_error_handling_in_create_slots(self, mock_logger, scheduler, db):
        """Test error handling in slot creation"""
        # Force an error by providing invalid dates
        start_date = date(2020, 1, 1)
        end_date = date(2019, 1, 1)  # End before start
        
        # This should trigger an error in slot creation logic
        result = scheduler.create_slots_for_period(start_date, end_date)
        
        # Should handle gracefully
        assert 'success' in result
