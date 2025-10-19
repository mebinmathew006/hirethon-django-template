"""
Simple unit tests to demonstrate pytest setup for the managers app
"""
import pytest
from datetime import timedelta

from hirethon_template.managers.models import Team
from .factories import TeamFactory, UserFactory, TeamMemberFactory


@pytest.mark.django_db
class TestSimpleModels:
    """Simple demonstration tests"""
    
    def test_team_creation_simple(self):
        """Test basic team creation works"""
        team = TeamFactory(name="Test Team")
        assert team.name == "Test Team"
        assert team.is_active is False
        assert team.slot_duration == timedelta(hours=1)
    
    def test_team_calculation_simple(self):
        """Test minimum members calculation works"""
        team = TeamFactory()
        min_members = team.calculate_minimum_members()
        assert isinstance(min_members, int)
        assert min_members > 0
    
    def test_team_with_members(self):
        """Test team with members"""
        team = TeamFactory()
        user = UserFactory()
        team_member = TeamMemberFactory(team=team, user=user)
        
        assert team_member.team == team
        assert team_member.user == user
        assert team_member.is_active is True
        
        # Test getting active member count
        assert team.get_active_member_count() == 1
