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
    max_hours_per_day = serializers.SerializerMethodField()
    max_hours_per_week = serializers.SerializerMethodField()
    min_rest_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'role',
            'skills',
            'date_joined',
            'last_login',
            'teams',
            'total_availability_hours',
            'max_hours_per_day',
            'max_hours_per_week',
            'min_rest_hours',
        ]
        read_only_fields = fields
    
    def get_teams(self, obj):
        """Get user's teams"""
        team_memberships = obj.team_memberships.filter(is_active=True)
        teams = [membership.team for membership in team_memberships]
        return UserDashboardTeamSerializer(teams, many=True).data
    
    def get_total_availability_hours(self, obj):
        """Calculate available hours for the user (assume available unless on leave)"""
        from datetime import date, timedelta
        
        today = date.today()
        # Calculate total days from today to next 30 days (or adjust as needed)
        total_days = 30
        
        # Count leave days (unavailable dates) in the next 30 days
        leave_days = obj.availability.filter(
            date__gte=today,
            date__lt=today + timedelta(days=total_days),
            is_available=False  # Only count unavailable/leave dates
        ).count()
        
        # Available days = total days - leave days
        available_days = total_days - leave_days
        
        # Convert to hours (assuming 24 hours per available day)
        return max(0, available_days * 24)
    
    def get_max_hours_per_day(self, obj):
        """Get max hours per day from user's primary team"""
        team_membership = obj.team_memberships.filter(is_active=True).first()
        if team_membership:
            return team_membership.team.max_hours_per_day
        return 8  # Default value
    
    def get_max_hours_per_week(self, obj):
        """Get max hours per week from user's primary team"""
        team_membership = obj.team_memberships.filter(is_active=True).first()
        if team_membership:
            return team_membership.team.max_hours_per_week
        return 40  # Default value
    
    def get_min_rest_hours(self, obj):
        """Get min rest hours from user's primary team"""
        team_membership = obj.team_memberships.filter(is_active=True).first()
        if team_membership:
            return team_membership.team.min_rest_hours
        return 8  # Default value
