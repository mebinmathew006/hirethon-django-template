"""
Unit tests for managers app models
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta, date

from hirethon_template.managers.models import (
    Team, TeamMember, Slot, Availability, Holiday, 
    LeaveRequest, SwapRequest, Alert
)
from hirethon_template.users.models import User
from .factories import (
    TeamFactory, TeamMemberFactory, SlotFactory, 
    AvailabilityFactory, HolidayFactory, LeaveRequestFactory,
    SwapRequestFactory, AlertFactory, UserFactory
)


@pytest.mark.django_db
class TestTeamModel:
    """Test Team model functionality"""
    def test_team_creation(self):
        """Test basic team creation"""
        team = TeamFactory(name="Test Team")
        assert team.name == "Test Team"
        assert team.slot_duration == timedelta(hours=1)
        assert team.max_hours_per_day == 8.0
        assert team.max_hours_per_week == 40.0
        assert team.min_rest_hours == 8.0
        assert team.is_active is False
    
    @pytest.mark.django_db
    def test_team_str_representation(self):
        """Test team string representation"""
        team = TeamFactory(name="My Team")
        assert str(team) == "My Team"
    
    @pytest.mark.django_db
    def test_calculate_minimum_members(self):
        """Test minimum members calculation"""
        team = TeamFactory(
            slot_duration=timedelta(hours=1),
            max_hours_per_day=8.0,
            max_hours_per_week=40.0,
            min_rest_hours=8.0
        )
        
        # Should return a positive integer
        min_members = team.calculate_minimum_members()
        assert isinstance(min_members, int)
        assert min_members > 0
    
    @pytest.mark.django_db
    def test_calculate_minimum_members_edge_cases(self):
        """Test minimum members calculation with edge cases"""
        # Very short slot duration
        team = TeamFactory(
            slot_duration=timedelta(minutes=30),
            max_hours_per_day=8.0,
            max_hours_per_week=40.0,
            min_rest_hours=8.0
        )
        min_members = team.calculate_minimum_members()
        assert min_members > 0
        
        # Very long slot duration
        team = TeamFactory(
            slot_duration=timedelta(hours=12),
            max_hours_per_day=8.0,
            max_hours_per_week=40.0,
            min_rest_hours=8.0
        )
        min_members = team.calculate_minimum_members()
        assert min_members > 0
    
    def test_get_active_member_count(self, db):
        """Test getting active member count"""
        team = TeamFactory()
        
        # No members initially
        assert team.get_active_member_count() == 0
        
        # Add active and inactive members
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        TeamMemberFactory(team=team, user=user1, is_active=True)
        TeamMemberFactory(team=team, user=user2, is_active=True)
        TeamMemberFactory(team=team, user=user3, is_active=False)
        
        assert team.get_active_member_count() == 2
    
    def test_update_active_status_becomes_active(self, db):
        """Test team becomes active when it has enough members"""
        team = TeamFactory(is_active=False)
        
        # Add enough active members to make team active
        min_required = team.calculate_minimum_members()
        
        # Create the required number of users and team members
        users = [UserFactory() for _ in range(min_required)]
        for user in users:
            TeamMemberFactory(team=team, user=user, is_active=True)
        
        # Update status
        status_changed = team.update_active_status()
        
        # Should have changed status and be active now
        assert status_changed is True
        team.refresh_from_db()
        assert team.is_active is True
    
    def test_update_active_status_stays_inactive(self, db):
        """Test team stays inactive when it doesn't have enough members"""
        team = TeamFactory(is_active=False)
        
        # Add fewer members than required
        min_required = team.calculate_minimum_members()
        required_members = max(1, min_required - 1)  # At least 1, but less than required
        
        users = [UserFactory() for _ in range(required_members)]
        for user in users:
            TeamMemberFactory(team=team, user=user, is_active=True)
        
        # Update status
        status_changed = team.update_active_status()
        
        # Should not have changed status and remain inactive
        assert status_changed is False
        team.refresh_from_db()
        assert team.is_active is False


@pytest.mark.django_db
class TestTeamMemberModel:
    """Test TeamMember model functionality"""
    
    def test_team_member_creation(self):
        """Test basic team member creation"""
        user = UserFactory()
        team = TeamFactory()
        
        team_member = TeamMemberFactory(user=user, team=team)
        
        assert team_member.user == user
        assert team_member.team == team
        assert team_member.is_manager is False
        assert team_member.is_active is True
    
    def test_team_member_unique_constraint(self, db):
        """Test that user can only be in a team once"""
        user = UserFactory()
        team = TeamFactory()
        
        # Create first membership
        TeamMemberFactory(user=user, team=team)
        
        # Should not be able to create duplicate
        with pytest.raises(IntegrityError):
            TeamMemberFactory(user=user, team=team)


@pytest.mark.django_db
class TestSlotModel:
    """Test Slot model functionality"""
    
    def test_slot_creation(self):
        """Test basic slot creation"""
        team = TeamFactory()
        start_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        slot = SlotFactory(team=team, start_time=start_time)
        
        assert slot.team == team
        assert slot.start_time == start_time
        assert slot.end_time == start_time + team.slot_duration
        assert slot.is_covered is False
        assert slot.assigned_member is None
    
    def test_slot_end_time_calculation(self):
        """Test slot end time is calculated correctly"""
        team = TeamFactory(slot_duration=timedelta(hours=2))
        start_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        slot = SlotFactory(team=team, start_time=start_time)
        
        expected_end_time = start_time + timedelta(hours=2)
        assert slot.end_time == expected_end_time


@pytest.mark.django_db
class TestAvailabilityModel:
    """Test Availability model functionality"""
    
    def test_availability_creation(self):
        """Test basic availability creation"""
        user = UserFactory()
        avail_date = timezone.now().date()
        
        availability = AvailabilityFactory(user=user, date=avail_date)
        
        assert availability.user == user
        assert availability.date == avail_date
        assert availability.is_available is True


@pytest.mark.django_db
class TestHolidayModel:
    """Test Holiday model functionality"""
    
    def test_holiday_creation(self):
        """Test basic holiday creation"""
        team = TeamFactory()
        holiday_date = timezone.now().date() + timedelta(days=30)
        
        holiday = HolidayFactory(team=team, date=holiday_date, description="Test Holiday")
        
        assert holiday.team == team
        assert holiday.date == holiday_date
        assert holiday.description == "Test Holiday"


@pytest.mark.django_db
class TestLeaveRequestModel:
    """Test LeaveRequest model functionality"""
    
    def test_leave_request_creation(self):
        """Test basic leave request creation"""
        user = UserFactory()
        team = TeamFactory()
        leave_date = timezone.now().date() + timedelta(days=1)
        
        leave_request = LeaveRequestFactory(
            user=user, 
            team=team, 
            date=leave_date,
            reason="Vacation",
            status="pending"
        )
        
        assert leave_request.user == user
        assert leave_request.team == team
        assert leave_request.date == leave_date
        assert leave_request.reason == "Vacation"
        assert leave_request.status == "pending"
    
    def test_leave_request_status_choices(self):
        """Test leave request status validation"""
        leave_request = LeaveRequestFactory(status="pending")
        assert leave_request.status in ["pending", "approved", "rejected"]


@pytest.mark.django_db
class TestSwapRequestModel:
    """Test SwapRequest model functionality"""
    
    def test_swap_request_creation(self):
        """Test basic swap request creation"""
        from_slot = SlotFactory()
        to_slot = SlotFactory(team=from_slot.team)  # Same team
        
        swap_request = SwapRequestFactory(
            from_slot=from_slot,
            to_slot=to_slot,
            reason="Need time off",
            status="pending"
        )
        
        assert swap_request.from_slot == from_slot
        assert swap_request.to_slot == to_slot
        assert swap_request.reason == "Need time off"
        assert swap_request.status == "pending"


@pytest.mark.django_db
class TestAlertModel:
    """Test Alert model functionality"""
    
    def test_alert_creation(self):
        """Test basic alert creation"""
        slot = SlotFactory()
        team = slot.team
        
        alert = AlertFactory(
            slot=slot,
            team=team,
            message="Test alert message"
        )
        
        assert alert.slot == slot
        assert alert.team == team
        assert alert.message == "Test alert message"
        assert alert.is_resolved is False
