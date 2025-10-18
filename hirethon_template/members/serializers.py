from rest_framework import serializers
from django.contrib.auth import get_user_model
from hirethon_template.managers.models import Team, TeamMember, Availability
from datetime import datetime

User = get_user_model()


class UserDashboardTeamSerializer(serializers.ModelSerializer):
    """
    Serializer for teams in user dashboard
    """
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'created_at',
            'is_active',
            'member_count',
        ]
        read_only_fields = fields
    
    def get_member_count(self, obj):
        """Get total number of members in this team"""
        return obj.members.count()


class UserDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer for user dashboard with team and availability info
    """
    teams = serializers.SerializerMethodField()
    total_availability_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'role',
            'skills',
            'max_hours_per_day',
            'max_hours_per_week',
            'min_rest_hours',
            'date_joined',
            'last_login',
            'teams',
            'total_availability_hours',
        ]
        read_only_fields = fields
    
    def get_teams(self, obj):
        """Get user's teams"""
        team_memberships = obj.team_memberships.filter(is_active=True)
        teams = [membership.team for membership in team_memberships]
        return UserDashboardTeamSerializer(teams, many=True).data
    
    def get_total_availability_hours(self, obj):
        """Get total available days for the user (since availability is now date-based)"""
        from datetime import date
        
        # Count available days from today onwards
        available_days = obj.availability.filter(
            is_available=True,  # Only count when user is available
            date__gte=date.today()
        ).count()
        
        # Convert to hours (assuming 24 hours per available day)
        return available_days * 24
