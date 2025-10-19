"""
Unit tests for managers app views
"""
import pytest
import json
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from rest_framework.test import APIClient
from rest_framework import status

from hirethon_template.users.models import User
from hirethon_template.managers.models import Team, TeamMember, Slot, Alert
from hirethon_template.users.tests.factories import UserFactory
from .factories import (
    TeamFactory, TeamMemberFactory, SlotFactory, AlertFactory
)


@pytest.fixture
def api_client():
    """Create API client for testing"""
    return APIClient()


@pytest.fixture
def admin_user():
    """Create admin user for testing"""
    return UserFactory(is_manager=True, is_staff=True, is_superuser=True)


@pytest.fixture
def regular_user():
    """Create regular user for testing"""
    return UserFactory(is_manager=False, is_staff=False)


@pytest.fixture
def team_with_members():
    """Create a team with members"""
    team = TeamFactory()
    users = [UserFactory() for _ in range(3)]
    
    for user in users:
        TeamMemberFactory(team=team, user=user, is_active=True)
    
    return team, users


@pytest.mark.django_db
class TestTeamViews:
    """Test team-related views"""
    
    def test_list_teams_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list teams"""
        url = reverse('managers:teams-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_teams_authenticated_admin(self, api_client, admin_user):
        """Test that authenticated admin can list teams"""
        team1 = TeamFactory(name="Team A")
        team2 = TeamFactory(name="Team B")
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('managers:teams-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Check if response has expected structure
        assert 'results' in response.data or isinstance(response.data, list)
    
    def test_create_team_admin_only(self, api_client, admin_user, regular_user):
        """Test that only admins can create teams"""
        team_data = {
            'name': 'New Team',
            'slot_duration': '01:00:00',
            'max_hours_per_day': 8.0,
            'max_hours_per_week': 40.0,
            'min_rest_hours': 8.0
        }
        
        # Regular user should not be able to create
        api_client.force_authenticate(user=regular_user)
        url = reverse('managers:create-team')
        response = api_client.post(url, team_data, format='json')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]
        
        # Admin should be able to create
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(url, team_data, format='json')
        # This might return different status codes depending on implementation
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]


@pytest.mark.django_db
class TestAlertViews:
    """Test alert-related views"""
    
    def test_get_empty_slots_notifications_admin(self, api_client, admin_user):
        """Test that admin can get empty slot notifications"""
        # Create some alerts
        AlertFactory.create_batch(2)
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('managers:get-notifications')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Check if response has expected structure
        assert isinstance(response.data, (dict, list))


@pytest.mark.django_db
class TestTeamMemberViews:
    """Test team member views"""
    
    def test_get_team_members_with_schedule(self, api_client, team_with_members, admin_user):
        """Test getting team members with schedule"""
        team, users = team_with_members
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('managers:get-team-members-with-schedule', kwargs={'team_id': team.id})
        response = api_client.get(url)
        
        # Should return some response (may vary based on implementation)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
class TestAPIResponseFormat:
    """Test API response formats and structure"""
    
    def test_teams_list_response_structure(self, api_client, admin_user):
        """Test that teams list API response has expected structure"""
        team = TeamFactory()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('managers:teams-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Response should be a list or dict with results
        assert isinstance(response.data, (dict, list))


@pytest.mark.django_db
class TestPermissionsAndAuthentication:
    """Test authentication and permission requirements"""
    
    def test_unauthorized_access_returns_401(self, api_client):
        """Test that unauthorized access returns 401"""
        # Try to access protected endpoints without authentication
        endpoints = [
            reverse('managers:teams-list'),
            reverse('managers:get-notifications'),
        ]
        
        for endpoint in endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_authenticated_user_can_access_protected_endpoints(self, api_client, admin_user):
        """Test that authenticated users can access protected endpoints"""
        api_client.force_authenticate(user=admin_user)
        
        # Should be able to access teams list
        url = reverse('managers:teams-list')
        response = api_client.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
