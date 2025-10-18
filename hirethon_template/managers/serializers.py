from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Team, TeamMember

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users
    """
    confirmPassword = serializers.CharField(write_only=True, help_text="Password confirmation")
    
    class Meta:
        model = User
        fields = [
            'name', 
            'email', 
            'password', 
            'confirmPassword',
            'is_manager', 
            'skills', 
            'max_hours_per_day', 
            'max_hours_per_week', 
            'min_rest_hours'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6},
            'name': {'required': True},
            'email': {'required': True},
            'skills': {'required': False, 'allow_null': True},
            'max_hours_per_day': {'required': False, 'min_value': 0},
            'max_hours_per_week': {'required': False, 'min_value': 0},
            'min_rest_hours': {'required': False, 'min_value': 0},
        }

    def validate_email(self, value):
        """
        Validate email uniqueness
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_password(self, value):
        """
        Validate password strength
        """
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value

    def validate_name(self, value):
        """
        Validate name field
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.strip()

    def validate(self, attrs):
        """
        Validate password confirmation and other cross-field validations
        """
        password = attrs.get('password')
        confirm_password = attrs.get('confirmPassword')
        
        if password != confirm_password:
            raise serializers.ValidationError({
                'confirmPassword': 'Passwords do not match.'
            })
        
        # Validate skills if provided
        skills = attrs.get('skills', [])
        if not isinstance(skills, list):
            raise serializers.ValidationError({
                'skills': 'Skills must be a list of strings.'
            })
        
        # Filter out empty skills and ensure they are strings
        if skills:
            filtered_skills = [skill.strip() for skill in skills if skill and str(skill).strip()]
            attrs['skills'] = filtered_skills
        
        # Validate work hours
        max_hours_per_day = attrs.get('max_hours_per_day', 8.0)
        max_hours_per_week = attrs.get('max_hours_per_week', 40.0)
        min_rest_hours = attrs.get('min_rest_hours', 8.0)
        
        # Validate reasonable hour limits
        if max_hours_per_day > 24:
            raise serializers.ValidationError({
                'max_hours_per_day': 'Daily hours cannot exceed 24 hours.'
            })
        
        if max_hours_per_week > 168:  # 24 * 7 = 168 hours in a week
            raise serializers.ValidationError({
                'max_hours_per_week': 'Weekly hours cannot exceed 168 hours.'
            })
        
        if max_hours_per_week < max_hours_per_day:
            raise serializers.ValidationError({
                'max_hours_per_week': 'Weekly hours cannot be less than daily hours.'
            })
        
        # Validate rest hours
        if min_rest_hours > max_hours_per_day:
            raise serializers.ValidationError({
                'min_rest_hours': 'Minimum rest hours cannot be greater than maximum daily hours.'
            })
        
        return attrs

    def create(self, validated_data):
        """
        Create and return a new user instance
        """
        # Remove confirmPassword from validated_data as it's not a model field
        validated_data.pop('confirmPassword', None)
        
        # Ensure skills is a list
        skills = validated_data.get('skills', [])
        if not isinstance(skills, list):
            skills = []
        
        user = User.objects.create_user(
            name=validated_data['name'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_manager=validated_data.get('is_manager', False),
            skills=skills,
            max_hours_per_day=validated_data.get('max_hours_per_day', 8.0),
            max_hours_per_week=validated_data.get('max_hours_per_week', 40.0),
            min_rest_hours=validated_data.get('min_rest_hours', 8.0),
        )
        
        return user


class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for user response data (read-only)
    """
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'is_active',
            'is_manager',
            'skills',
            'max_hours_per_day',
            'max_hours_per_week',
            'min_rest_hours',
            'date_joined'
        ]
        read_only_fields = fields


class CreateTeamSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new teams
    """
    slot_duration = serializers.IntegerField(help_text="Slot duration in seconds")
    
    class Meta:
        model = Team
        fields = [
            'name',
            'slot_duration',
        ]
        extra_kwargs = {
            'name': {'required': True},
            'slot_duration': {'required': True, 'min_value': 1},
        }

    def validate_name(self, value):
        """
        Validate team name
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Team name is required.")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Team name must be at least 3 characters long.")
        
        # Check if team with this name already exists
        if Team.objects.filter(name__iexact=value.strip()).exists():
            raise serializers.ValidationError("A team with this name already exists.")
        
        return value.strip()

    def validate_slot_duration(self, value):
        """
        Validate slot duration
        """
        if value <= 0:
            raise serializers.ValidationError("Slot duration must be greater than 0 seconds.")
        
        # Reasonable limits for slot duration (1 minute to 24 hours)
        if value < 60:
            raise serializers.ValidationError("Slot duration must be at least 1 minute (60 seconds).")
        if value > 86400:  # 24 hours
            raise serializers.ValidationError("Slot duration cannot exceed 24 hours.")
        
        return value

    def create(self, validated_data):
        """
        Create and return a new team instance
        """
        # Convert seconds to timedelta for the DurationField
        slot_duration_seconds = validated_data.pop('slot_duration')
        validated_data['slot_duration'] = timedelta(seconds=slot_duration_seconds)
        
        team = Team.objects.create(**validated_data)
        return team


class TeamResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for team response data (read-only)
    """
    slot_duration_seconds = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'slot_duration',
            'slot_duration_seconds',
            'created_at',
            'member_count',
        ]
        read_only_fields = fields

    def get_slot_duration_seconds(self, obj):
        """Convert timedelta to seconds for easier frontend consumption"""
        return int(obj.slot_duration.total_seconds())

    def get_member_count(self, obj):
        """Get the number of members in this team"""
        return obj.members.count()


class CreateTeamMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for adding team members to teams
    """
    
    class Meta:
        model = TeamMember
        fields = [
            'user',
            'team',
            'is_manager',
        ]
        extra_kwargs = {
            'user': {'required': True},
            'team': {'required': True},
            'is_manager': {'required': False, 'default': False},
        }

    def validate_user(self, value):
        """
        Validate that the user is not a manager (only regular users can be team members)
        """
        if value.is_manager:
            raise serializers.ValidationError("Users with manager role cannot be assigned as team members.")
        
        if not value.is_active:
            raise serializers.ValidationError("Only active users can be assigned to teams.")
        
        return value

    def validate(self, attrs):
        """
        Validate that the user is not already a member of this team
        """
        user = attrs.get('user')
        team = attrs.get('team')
        
        if user and team:
            if TeamMember.objects.filter(user=user, team=team).exists():
                raise serializers.ValidationError({
                    'commonError': 'This user is already a member of this team.'
                })
        
        return attrs

    def create(self, validated_data):
        """
        Create and return a new team member instance
        """
        team_member = TeamMember.objects.create(**validated_data)
        return team_member


class TeamMemberResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for team member response data (read-only)
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_id = serializers.IntegerField(source='team.id', read_only=True)
    
    class Meta:
        model = TeamMember
        fields = [
            'id',
            'user_id',
            'user_name',
            'user_email',
            'team_id',
            'team_name',
            'is_manager',
        ]
        read_only_fields = fields


class TeamListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing teams in dropdowns
    """
    
    class Meta:
        model = Team
        fields = [
            'id',
            'name',
        ]
        read_only_fields = fields


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users in dropdowns (non-managers only)
    """
    
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
        ]
        read_only_fields = fields
