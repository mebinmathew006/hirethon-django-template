from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import Team
from .serializers import (
    CreateUserSerializer, UserResponseSerializer, 
    CreateTeamSerializer, TeamResponseSerializer,
    CreateTeamMemberSerializer, TeamMemberResponseSerializer,
    TeamListSerializer, UserListSerializer
)
from .tasks import send_user_credentials_email_task

User = get_user_model()

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user_view(request):
    """
    API view to create a new user (only accessible by authenticated managers/admins)
    """
    # Check if the requesting user has permission to create users
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to create users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Use serializer for validation and creation
    serializer = CreateUserSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Get the password before it's hashed by the serializer
            user_password = serializer.validated_data.get('password')
            user_email = serializer.validated_data.get('email')
            user_name = serializer.validated_data.get('name')
            is_manager = serializer.validated_data.get('is_manager', False)
            
            # Create the user using the serializer
            user = serializer.save()
            
            # Trigger email sending as a background task
            send_user_credentials_email_task.delay(
                user_email=user_email,
                user_name=user_name,
                password=user_password,
                is_manager=is_manager
            )
            
            # Serialize the response data
            response_serializer = UserResponseSerializer(user)
            
            return Response({
                'message': 'User created successfully. Credentials will be sent via email.',
                'user': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': {'commonError': 'An unexpected error occurred while creating the user.'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # Return validation errors in the expected format for frontend
        errors = {}
        common_errors = []
        
        for field, field_errors in serializer.errors.items():
            if isinstance(field_errors, list):
                error_message = field_errors[0] if field_errors else ''
                if field in ['name', 'email', 'password', 'confirmPassword', 'is_manager', 'skills']:
                    errors[field] = error_message
                else:
                    common_errors.append(error_message)
            else:
                error_message = str(field_errors)
                if field in ['name', 'email', 'password', 'confirmPassword', 'is_manager', 'skills']:
                    errors[field] = error_message
                else:
                    common_errors.append(error_message)
        
        # Add common errors if any
        if common_errors:
            errors['commonError'] = common_errors[0] if len(common_errors) == 1 else '; '.join(common_errors)
        
        return Response(
            {'error': errors},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_team_view(request):
    """
    API view to create a new team (only accessible by authenticated managers/admins)
    """
    # Check if the requesting user has permission to create teams
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to create teams.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Use serializer for validation and creation
    serializer = CreateTeamSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Create the team using the serializer
            team = serializer.save()
            
            # Serialize the response data
            response_serializer = TeamResponseSerializer(team)
            
            return Response({
                'message': 'Team created successfully.',
                'team': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': {'commonError': 'An unexpected error occurred while creating the team.'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # Return validation errors in the expected format for frontend
        errors = {}
        common_errors = []
        
        for field, field_errors in serializer.errors.items():
            if isinstance(field_errors, list):
                error_message = field_errors[0] if field_errors else ''
                if field in ['name', 'slot_duration']:
                    errors[field] = error_message
                else:
                    common_errors.append(error_message)
            else:
                error_message = str(field_errors)
                if field in ['name', 'slot_duration']:
                    errors[field] = error_message
                else:
                    common_errors.append(error_message)
        
        # Add common errors if any
        if common_errors:
            errors['commonError'] = common_errors[0] if len(common_errors) == 1 else '; '.join(common_errors)
        
        return Response(
            {'error': errors},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teams_list_view(request):
    """
    API view to get list of teams for dropdowns (only accessible by authenticated managers/admins)
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view teams.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    teams = Team.objects.all().order_by('name')
    serializer = TeamListSerializer(teams, many=True)
    
    return Response({
        'teams': serializer.data
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users_list_view(request):
    """
    API view to get list of users (non-managers) for dropdowns (only accessible by authenticated managers/admins)
    """
    # Debug logging
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User ID: {request.user.id if hasattr(request.user, 'id') else 'No ID'}")
    print(f"User email: {getattr(request.user, 'email', 'No email')}")
    print(f"User is_superuser: {getattr(request.user, 'is_superuser', 'No is_superuser')}")
    print(f"User is_manager: {getattr(request.user, 'is_manager', 'No is_manager')}")
    
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get only active users who are not managers
    users = User.objects.filter(is_active=True, is_manager=False).order_by('name')
    serializer = UserListSerializer(users, many=True)
    
    return Response({
        'users': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_team_member_view(request):
    """
    API view to add a user as a team member (only accessible by authenticated managers/admins)
    """
    # Check if the requesting user has permission to assign team members
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to assign team members.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Use serializer for validation and creation
    serializer = CreateTeamMemberSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Create the team member using the serializer
            team_member = serializer.save()
            
            # Serialize the response data
            response_serializer = TeamMemberResponseSerializer(team_member)
            
            return Response({
                'message': 'User added to team successfully.',
                'team_member': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': {'commonError': 'An unexpected error occurred while adding the team member.'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # Return validation errors in the expected format for frontend
        errors = {}
        common_errors = []
        
        for field, field_errors in serializer.errors.items():
            if isinstance(field_errors, list):
                error_message = field_errors[0] if field_errors else ''
                if field in ['user', 'team', 'is_manager']:
                    errors[field] = error_message
                else:
                    common_errors.append(error_message)
            else:
                error_message = str(field_errors)
                if field in ['user', 'team', 'is_manager']:
                    errors[field] = error_message
                else:
                    common_errors.append(error_message)
        
        # Check for common error in validate method
        if 'commonError' in serializer.errors:
            common_errors.append(serializer.errors['commonError'])
        
        # Add common errors if any
        if common_errors:
            errors['commonError'] = common_errors[0] if len(common_errors) == 1 else '; '.join(common_errors)
        
        return Response(
            {'error': errors},
            status=status.HTTP_400_BAD_REQUEST
        )