from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

from .models import Team, TeamMember, LeaveRequest, Slot, SwapRequest
from .serializers import (
    CreateUserSerializer, UserResponseSerializer, 
    CreateTeamSerializer, TeamResponseSerializer,
    CreateTeamMemberSerializer, TeamMemberResponseSerializer,
    TeamListSerializer, TeamManagementSerializer, UserListSerializer, UserManagementSerializer
)
from .tasks import send_user_credentials_email_task

User = get_user_model()

# Helper function to check if user is active
def check_user_activity(user):
    """
    Check if user is active, return error response if not
    """
    if not user.is_active:
        from rest_framework.response import Response
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    return None

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user_view(request):
    """
    API view to create a new user (only accessible by authenticated managers/admins)
    """
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
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
            try:
                print(f"Triggering email task for new user: {user_email}")
                task_result = send_user_credentials_email_task.delay(
                    user_email=user_email,
                    user_name=user_name,
                    password=user_password,
                    is_manager=is_manager
                )
                print(f"Email task queued successfully: {task_result.id}")
            except Exception as e:
                print(f"Failed to queue email task for {user_email}: {str(e)}")
                # Fallback: try to send email synchronously
                try:
                    from hirethon_template.utils.email import send_user_credentials_email
                    print(f"Attempting synchronous email sending for {user_email}")
                    send_user_credentials_email(
                        user_email=user_email,
                        user_name=user_name,
                        password=user_password,
                        is_manager=is_manager
                    )
                    print(f"Synchronous email sent successfully to {user_email}")
                except Exception as sync_e:
                    print(f"Synchronous email also failed for {user_email}: {str(sync_e)}")
                # Don't fail the user creation if email task fails
            
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users_management_view(request):
    """
    API view to get all users with management info (with pagination)
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get pagination parameters from query string
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 10
    
    # Ensure page_size is within reasonable limits
    page_size = min(max(page_size, 1), 50)  # Between 1 and 50
    
    users_queryset = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users_queryset, page_size)
    
    try:
        users_page = paginator.page(page)
    except:
        # If page is out of range, return the last page
        users_page = paginator.page(paginator.num_pages)
    
    serializer = UserManagementSerializer(users_page.object_list, many=True)
    
    return Response({
        'users': serializer.data,
        'pagination': {
            'current_page': users_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': users_page.has_next(),
            'has_previous': users_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_user_status_view(request, user_id):
    """
    API view to toggle user active status
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to modify users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Prevent users from deactivating themselves
    if request.user.id == user_id:
        return Response(
            {'error': {'commonError': 'You cannot deactivate your own account.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
         user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': {'commonError': 'User not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Prevent deactivating superusers
    if user.is_superuser and not request.user.is_superuser:
        return Response(
            {'error': {'commonError': 'You cannot deactivate superuser accounts.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Toggle the is_active status
    user.is_active = not user.is_active
    user.save()
    
    serializer = UserManagementSerializer(user)
    
    return Response({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully.',
        'user': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_team_view(request):
    """
    API view to create a new team (only accessible by authenticated managers/admins)
    """
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
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
                if field in ['name', 'slot_duration', 'max_hours_per_day', 'max_hours_per_week', 'min_rest_hours']:
                    errors[field] = error_message
                else:
                    common_errors.append(error_message)
            else:
                error_message = str(field_errors)
                if field in ['name', 'slot_duration', 'max_hours_per_day', 'max_hours_per_week', 'min_rest_hours']:
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
def get_users_management_view(request):
    """
    API view to get all users with management info (with pagination)
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get pagination parameters from query string
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 10
    
    # Ensure page_size is within reasonable limits
    page_size = min(max(page_size, 1), 50)  # Between 1 and 50
    
    users_queryset = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users_queryset, page_size)
    
    try:
        users_page = paginator.page(page)
    except:
        # If page is out of range, return the last page
        users_page = paginator.page(paginator.num_pages)
    
    serializer = UserManagementSerializer(users_page.object_list, many=True)
    
    return Response({
        'users': serializer.data,
        'pagination': {
            'current_page': users_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': users_page.has_next(),
            'has_previous': users_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_user_status_view(request, user_id):
    """
    API view to toggle user active status
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to modify users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Prevent users from deactivating themselves
    if request.user.id == user_id:
        return Response(
            {'error': {'commonError': 'You cannot deactivate your own account.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
         user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': {'commonError': 'User not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Prevent deactivating superusers
    if user.is_superuser and not request.user.is_superuser:
        return Response(
            {'error': {'commonError': 'You cannot deactivate superuser accounts.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Toggle the is_active status
    user.is_active = not user.is_active
    user.save()
    
    serializer = UserManagementSerializer(user)
    
    return Response({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully.',
        'user': serializer.data
    }, status=status.HTTP_200_OK)


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
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get only active users who are not managers and not already in any team
    users_in_teams = TeamMember.objects.values_list('user_id', flat=True)
    users = User.objects.filter(
        is_active=True, 
        is_manager=False
    ).exclude(
        id__in=users_in_teams
    ).order_by('name')
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users_management_view(request):
    """
    API view to get all users with management info (with pagination)
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get pagination parameters from query string
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 10
    
    # Ensure page_size is within reasonable limits
    page_size = min(max(page_size, 1), 50)  # Between 1 and 50
    
    users_queryset = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users_queryset, page_size)
    
    try:
        users_page = paginator.page(page)
    except:
        # If page is out of range, return the last page
        users_page = paginator.page(paginator.num_pages)
    
    serializer = UserManagementSerializer(users_page.object_list, many=True)
    
    return Response({
        'users': serializer.data,
        'pagination': {
            'current_page': users_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': users_page.has_next(),
            'has_previous': users_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_user_status_view(request, user_id):
    """
    API view to toggle user active status
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to modify users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Prevent users from deactivating themselves
    if request.user.id == user_id:
        return Response(
            {'error': {'commonError': 'You cannot deactivate your own account.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
         user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': {'commonError': 'User not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Prevent deactivating superusers
    if user.is_superuser and not request.user.is_superuser:
        return Response(
            {'error': {'commonError': 'You cannot deactivate superuser accounts.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Toggle the is_active status
    user.is_active = not user.is_active
    user.save()
    
    serializer = UserManagementSerializer(user)
    
    return Response({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully.',
        'user': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teams_management_view(request):
    """
    API view to get all teams with management info (member counts, status) with pagination
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view teams.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get pagination parameters from query string
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 10
    
    # Ensure page_size is within reasonable limits
    page_size = min(max(page_size, 1), 50)  # Between 1 and 50
    
    teams_queryset = Team.objects.all().order_by('-created_at')
    paginator = Paginator(teams_queryset, page_size)
    
    try:
        teams_page = paginator.page(page)
    except:
        # If page is out of range, return the last page
        teams_page = paginator.page(paginator.num_pages)
    
    serializer = TeamManagementSerializer(teams_page.object_list, many=True)
    
    return Response({
        'teams': serializer.data,
        'pagination': {
            'current_page': teams_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': teams_page.has_next(),
            'has_previous': teams_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_team_status_view(request, team_id):
    """
    API view to toggle team active status
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to modify teams.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return Response(
            {'error': {'commonError': 'Team not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Toggle the is_active status
    team.is_active = not team.is_active
    team.save()
    
    serializer = TeamManagementSerializer(team)
    
    return Response({
        'message': f'Team {"activated" if team.is_active else "deactivated"} successfully.',
        'team': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_team_member_for_team_view(request, team_id):
    """
    API view to add a user as a team member for a specific team (only accessible by authenticated managers/admins)
    """
    # Check if the requesting user has permission to assign team members
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to assign team members.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Verify team exists
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return Response(
            {'error': {'commonError': 'Team not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Add team_id to request data
    data = request.data.copy()
    data['team'] = team_id
    
    # Check if user is already a member of this team
    user_id = request.data.get('user')
    if user_id:
        try:
            existing_membership = TeamMember.objects.get(user_id=user_id, team=team)
            if existing_membership.is_active:
                return Response(
                    {'error': {'commonError': 'This user is already an active member of this team.'}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Reactivate the existing membership
                existing_membership.is_active = True
                existing_membership.save()
                response_serializer = TeamMemberResponseSerializer(existing_membership)
                return Response({
                    'message': 'User reactivated in team successfully.',
                    'team_member': response_serializer.data
                }, status=status.HTTP_200_OK)
        except TeamMember.DoesNotExist:
            pass  # User is not a member of this team, continue with creation
    
    # Use serializer for validation and creation
    serializer = CreateTeamMemberSerializer(data=data)
    
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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating team member: {str(e)}")
            
            # Check if it's a unique constraint violation
            if 'unique constraint' in str(e).lower() or 'unique set' in str(e).lower():
                return Response(
                    {'error': {'commonError': 'This user is already a member of this team.'}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users_management_view(request):
    """
    API view to get all users with management info (with pagination)
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to view users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get pagination parameters from query string
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 10
    
    # Ensure page_size is within reasonable limits
    page_size = min(max(page_size, 1), 50)  # Between 1 and 50
    
    users_queryset = User.objects.filter(is_superuser=False).order_by('-date_joined')
    paginator = Paginator(users_queryset, page_size)
    
    try:
        users_page = paginator.page(page)
    except:
        # If page is out of range, return the last page
        users_page = paginator.page(paginator.num_pages)
    
    serializer = UserManagementSerializer(users_page.object_list, many=True)
    
    return Response({
        'users': serializer.data,
        'pagination': {
            'current_page': users_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': users_page.has_next(),
            'has_previous': users_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_user_status_view(request, user_id):
    """
    API view to toggle user active status
    """
    if not (request.user.is_superuser or request.user.is_manager):
        return Response(
            {'error': {'commonError': 'You do not have permission to modify users.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Prevent users from deactivating themselves
    if request.user.id == user_id:
        return Response(
            {'error': {'commonError': 'You cannot deactivate your own account.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
         user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': {'commonError': 'User not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Prevent deactivating superusers
    if user.is_superuser and not request.user.is_superuser:
        return Response(
            {'error': {'commonError': 'You cannot deactivate superuser accounts.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Toggle the is_active status
    user.is_active = not user.is_active
    user.save()
    
    serializer = UserManagementSerializer(user)
    
    return Response({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully.',
        'user': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_empty_slots_notifications_view(request):
    """
    API view to get empty slots notifications for admin dashboard
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can view notifications.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from django.core.cache import cache
        from .models import Alert
        
        # Get notifications from cache
        notifications = cache.get("empty_slots_notifications", [])
        
        # Get alerts from database (unresolved, recent)
        from datetime import timedelta
        from django.utils import timezone
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        alerts = Alert.objects.filter(
            resolved=False,
            created_at__gte=cutoff_time
        ).select_related('team', 'slot').order_by('-created_at')
        
        # Convert alerts to notification format for consistency
        # Only include alerts for slots that are actually still empty
        alert_notifications = []
        for alert in alerts:
            # Check if the slot is still empty
            if alert.slot.assigned_member is None:
                hours_from_now = round((alert.slot.start_time - timezone.now()).total_seconds() / 3600, 1)
                alert_notifications.append({
                    'slot_id': alert.slot.id,
                    'team_id': alert.team.id,
                    'team_name': alert.team.name,
                    'start_time': alert.slot.start_time.isoformat(),
                    'end_time': alert.slot.end_time.isoformat(),
                    'notification_time': alert.created_at.isoformat(),
                    'type': 'empty_slot_alert',
                    'alert_id': alert.id,
                    'message': alert.message,
                    'hours_from_now': hours_from_now,
                    'is_empty': True,
                    'assigned_user': None
                })
            else:
                # Mark the alert as resolved since the slot is no longer empty
                alert.resolved = True
                alert.save()
        
        # Filter out old cache notifications (older than 24 hours) and validate slots are still empty
        from datetime import datetime
        recent_cache_notifications = []
        
        for notification in notifications:
            try:
                notification_time = datetime.fromisoformat(
                    notification.get('notification_time', '').replace('Z', '+00:00')
                )
                if timezone.is_naive(notification_time):
                    notification_time = timezone.make_aware(notification_time)
                
                # Only include recent notifications
                if notification_time >= cutoff_time:
                    # Validate that the slot is still empty
                    slot_id = notification.get('slot_id')
                    if slot_id:
                        try:
                            from .models import Slot
                            slot = Slot.objects.get(id=slot_id)
                            if slot.assigned_member is None:
                                # Add is_empty field to make it explicit
                                notification['is_empty'] = True
                                notification['assigned_user'] = None
                                recent_cache_notifications.append(notification)
                        except Slot.DoesNotExist:
                            # Slot doesn't exist anymore, skip this notification
                            continue
                    else:
                        # No slot_id, skip this notification
                        continue
            except (ValueError, TypeError):
                # Skip invalid timestamps
                continue
        
        # Update cache with filtered notifications (only truly empty slots)
        cache.set("empty_slots_notifications", recent_cache_notifications, 86400)
        
        # Combine cache notifications and alert notifications
        all_notifications = recent_cache_notifications + alert_notifications
        
        return Response({
            'notifications': all_notifications,
            'count': len(all_notifications),
            'cache_notifications': len(recent_cache_notifications),
            'alert_notifications': len(alert_notifications)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching notifications: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to fetch notifications.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read_view(request):
    """
    API view to mark a notification as read
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can mark notifications as read.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from django.core.cache import cache
        from .models import Alert
        
        notification_id = request.data.get('notification_id')
        alert_id = request.data.get('alert_id')
        
        if not notification_id and not alert_id:
            return Response(
                {'error': {'commonError': 'Notification ID or Alert ID is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle alert resolution if alert_id is provided
        if alert_id:
            try:
                alert = Alert.objects.get(id=alert_id, resolved=False)
                alert.resolved = True
                alert.save()
            except Alert.DoesNotExist:
                return Response(
                    {'error': {'commonError': 'Alert not found or already resolved.'}},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Handle cache notification removal if notification_id is provided
        if notification_id:
            # Get current notifications
            notifications = cache.get("empty_slots_notifications", [])
            
            # Remove the notification with the given ID
            updated_notifications = [
                n for n in notifications 
                if n.get('slot_id') != notification_id
            ]
            
            # Update cache
            cache.set("empty_slots_notifications", updated_notifications, 86400)
            
            return Response({
                'message': 'Notification marked as read.',
                'remaining_cache_count': len(updated_notifications)
            }, status=status.HTTP_200_OK)
        
        # If only alert_id was provided
        return Response({
            'message': 'Alert marked as resolved.',
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error marking notification as read: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to mark notification as read.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leave_requests_view(request):
    """
    API view to get all pending leave requests for admin approval
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can view leave requests.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Get query parameters
        status_filter = request.GET.get('status', 'pending')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Build queryset
        queryset = LeaveRequest.objects.select_related('user', 'team').order_by('-requested_at')
        
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        # Paginate results
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        leave_requests_data = []
        for leave_request in page_obj:
            # Count user's slots for that date
            user_slots_count = Slot.objects.filter(
                assigned_member=leave_request.user,
                start_time__date=leave_request.date,
                team=leave_request.team
            ).count()
            
            leave_requests_data.append({
                'id': leave_request.id,
                'user': {
                    'id': leave_request.user.id,
                    'name': leave_request.user.name,
                    'email': leave_request.user.email
                },
                'team': {
                    'id': leave_request.team.id,
                    'name': leave_request.team.name
                },
                'date': leave_request.date.isoformat(),
                'reason': leave_request.reason,
                'status': leave_request.status,
                'requested_at': leave_request.requested_at.isoformat(),
                'reviewed_at': leave_request.reviewed_at.isoformat() if leave_request.reviewed_at else None,
                'reviewed_by': {
                    'id': leave_request.reviewed_by.id,
                    'name': leave_request.reviewed_by.name
                } if leave_request.reviewed_by else None,
                'slots_count': user_slots_count
            })
        
        return Response({
            'leave_requests': leave_requests_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching leave requests: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to fetch leave requests.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_reject_leave_request_view(request, leave_request_id):
    """
    API view to approve or reject a leave request
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can approve/reject leave requests.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from django.utils import timezone
        from hirethon_template.managers.models import Availability
        
        action = request.data.get('action')  # 'approve' or 'reject'
        
        if action not in ['approve', 'reject']:
            return Response(
                {'error': {'commonError': 'Action must be either "approve" or "reject".'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            leave_request = LeaveRequest.objects.get(
                id=leave_request_id,
                status='pending'
            )
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': {'commonError': 'Leave request not found or already processed.'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update the leave request
        leave_request.status = 'approved' if action == 'approve' else 'rejected'
        leave_request.reviewed_at = timezone.now()
        leave_request.reviewed_by = request.user
        leave_request.save()
        
        if action == 'approve':
            # Create availability record to mark user as unavailable
            availability, created = Availability.objects.update_or_create(
                user=leave_request.user,
                date=leave_request.date,
                defaults={
                    'is_available': False,
                    'reason': f"Approved leave: {leave_request.reason}"
                }
            )
            
            # Remove user from all slots for that date and team
            slots_to_update = Slot.objects.filter(
                assigned_member=leave_request.user,
                start_time__date=leave_request.date,
                team=leave_request.team
            )
            
            slots_updated = 0
            for slot in slots_to_update:
                slot.assigned_member = None
                slot.save()
                slots_updated += 1
            
            return Response({
                'message': f'Leave request approved successfully. Removed user from {slots_updated} slots.',
                'leave_request': {
                    'id': leave_request.id,
                    'status': leave_request.status,
                    'reviewed_at': leave_request.reviewed_at.isoformat(),
                    'reviewed_by': leave_request.reviewed_by.name,
                    'slots_updated': slots_updated
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Leave request rejected successfully.',
                'leave_request': {
                    'id': leave_request.id,
                    'status': leave_request.status,
                    'reviewed_at': leave_request.reviewed_at.isoformat(),
                    'reviewed_by': leave_request.reviewed_by.name
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing leave request: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to process leave request.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_users_for_slot_view(request, slot_id):
    """
    API view to get available users for a specific slot (users who are not on leave for that date)
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can view available users for slots.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from datetime import date
        from hirethon_template.managers.models import Availability
        
        # Get the slot
        try:
            slot = Slot.objects.select_related('team').get(id=slot_id)
        except Slot.DoesNotExist:
            return Response(
                {'error': {'commonError': 'Slot not found.'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        slot_date = slot.start_time.date()
        
        # Get all active team members for this team
        team_members = User.objects.filter(
            team_memberships__team=slot.team,
            team_memberships__is_active=True,
            is_active=True
        ).distinct()
        
        # Filter out users who are on leave for this date
        users_on_leave = Availability.objects.filter(
            user__in=team_members,
            date=slot_date,
            is_available=False
        ).values_list('user_id', flat=True)
        
        available_users = team_members.exclude(
            id__in=users_on_leave
        ).values('id', 'name', 'email')
        
        return Response({
            'slot': {
                'id': slot.id,
                'team_name': slot.team.name,
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'date': slot_date.isoformat()
            },
            'available_users': list(available_users)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching available users for slot: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to fetch available users for slot.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_user_to_slot_view(request, slot_id):
    """
    API view to assign a user to a specific slot
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can assign users to slots.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from datetime import date
        from hirethon_template.managers.models import Availability
        
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': {'commonError': 'User ID is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the slot
        try:
            slot = Slot.objects.select_related('team', 'assigned_member').get(id=slot_id)
        except Slot.DoesNotExist:
            return Response(
                {'error': {'commonError': 'Slot not found.'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if slot is already assigned
        if slot.assigned_member:
            return Response(
                {'error': {'commonError': 'Slot is already assigned to a user.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': {'commonError': 'User not found.'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user is in the team
        if not TeamMember.objects.filter(
            team=slot.team,
            user=user,
            is_active=True
        ).exists():
            return Response(
                {'error': {'commonError': 'User is not a member of this team.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is available on this date (not on leave)
        slot_date = slot.start_time.date()
        try:
            availability = Availability.objects.get(user=user, date=slot_date)
            if not availability.is_available:
                return Response(
                    {'error': {'commonError': 'User is on leave for this date.'}},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Availability.DoesNotExist:
            # If no availability record, user is available by default
            pass
        
        # Assign the user to the slot
        slot.assigned_member = user
        slot.save()
        
        # Mark any related alerts as resolved since the slot is no longer empty
        from .models import Alert
        Alert.objects.filter(
            slot=slot,
            resolved=False
        ).update(resolved=True)
        
        # Also remove any cache notifications for this slot
        from django.core.cache import cache
        notifications = cache.get("empty_slots_notifications", [])
        updated_notifications = [
            n for n in notifications 
            if n.get('slot_id') != slot.id
        ]
        cache.set("empty_slots_notifications", updated_notifications, 86400)
        
        return Response({
            'message': 'User assigned to slot successfully.',
            'slot': {
                'id': slot.id,
                'assigned_member': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email
                },
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'team_name': slot.team.name
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error assigning user to slot: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to assign user to slot.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_team_members_with_schedule_view(request, team_id):
    """
    API view to get team members with their 1-week schedule
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can view team member schedules.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from datetime import timedelta
        from django.utils import timezone
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Get the team
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response(
                {'error': {'commonError': 'Team not found.'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get active team members
        team_members = User.objects.filter(
            team_memberships__team=team,
            team_memberships__is_active=True,
            is_active=True
        ).distinct()
        
        # Paginate team members
        paginator = Paginator(team_members, page_size)
        page_obj = paginator.get_page(page)
        
        # Calculate date range (next 7 days from today)
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        
        members_data = []
        for member in page_obj:
            # Get member's slots for the next 7 days
            member_slots = Slot.objects.filter(
                assigned_member=member,
                start_time__date__gte=today,
                start_time__date__lt=end_date,
                team=team
            ).order_by('start_time')
            
            # Format slots data
            slots_data = []
            for slot in member_slots:
                slots_data.append({
                    'id': slot.id,
                    'start_time': slot.start_time.isoformat(),
                    'end_time': slot.end_time.isoformat(),
                    'date': slot.start_time.date().isoformat(),
                    'duration_hours': round((slot.end_time - slot.start_time).total_seconds() / 3600, 1),
                    'is_holiday': slot.is_holiday
                })
            
            # Get member's availability for the next 7 days
            from hirethon_template.managers.models import Availability
            availability_data = []
            for i in range(7):
                check_date = today + timedelta(days=i)
                try:
                    availability = Availability.objects.get(user=member, date=check_date)
                    availability_data.append({
                        'date': check_date.isoformat(),
                        'is_available': availability.is_available,
                        'reason': availability.reason
                    })
                except Availability.DoesNotExist:
                    # Default to available if no record exists
                    availability_data.append({
                        'date': check_date.isoformat(),
                        'is_available': True,
                        'reason': ''
                    })
            
            members_data.append({
                'id': member.id,
                'name': member.name,
                'email': member.email,
                'is_active': member.is_active,
                'slots': slots_data,
                'total_slots': len(slots_data),
                'availability': availability_data
            })
        
        return Response({
            'team': {
                'id': team.id,
                'name': team.name
            },
            'members': members_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'date_range': {
                'start_date': today.isoformat(),
                'end_date': end_date.isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching team members with schedule: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to fetch team members with schedule.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats_view(request):
    """
    API view to get dashboard statistics for admin homepage
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can view dashboard statistics.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from django.utils import timezone
        from datetime import timedelta, datetime
        
        # Get current date and calculate date ranges
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Calculate statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        total_teams = Team.objects.count()
        active_teams = Team.objects.filter(is_active=True).count()
        
        total_managers = User.objects.filter(is_manager=True).count()
        active_managers = User.objects.filter(is_manager=True, is_active=True).count()
        
        # Calculate average hours per week (from slots)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        weekly_slots = Slot.objects.filter(
            start_time__date__gte=start_of_week,
            start_time__date__lte=end_of_week,
            assigned_member__isnull=False
        )
        
        total_hours = 0
        slot_count = 0
        for slot in weekly_slots:
            duration = (slot.end_time - slot.start_time).total_seconds() / 3600
            total_hours += duration
            slot_count += 1
        
        avg_hours_per_week = round(total_hours, 1) if slot_count > 0 else 0
        
        # Recent activity data (last 7 days)
        recent_activities = []
        
        # Recent team creation
        recent_teams = Team.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:5]
        for team in recent_teams:
            recent_activities.append({
                'type': 'team_created',
                'team_name': team.name,
                'created_at': team.created_at.isoformat(),
                'created_by': 'System',  # We don't track who created teams currently
                'time_ago': format_time_ago(team.created_at)
            })
        
        # Recent user creation
        recent_users = User.objects.filter(date_joined__gte=week_ago).order_by('-date_joined')[:5]
        for user in recent_users:
            recent_activities.append({
                'type': 'user_created',
                'user_name': user.name,
                'created_at': user.date_joined.isoformat(),
                'created_by': 'System',
                'time_ago': format_time_ago(user.date_joined)
            })
        
        # Recent leave requests
        recent_leave_requests = LeaveRequest.objects.filter(
            requested_at__gte=week_ago
        ).select_related('user', 'team').order_by('-requested_at')[:5]
        
        for leave_request in recent_leave_requests:
            recent_activities.append({
                'type': 'leave_requested',
                'user_name': leave_request.user.name,
                'team_name': leave_request.team.name,
                'date': leave_request.date.isoformat(),
                'status': leave_request.status,
                'created_at': leave_request.requested_at.isoformat(),
                'time_ago': format_time_ago(leave_request.requested_at)
            })
        
        # Sort activities by created_at descending and get top 10
        recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
        recent_activities = recent_activities[:10]
        
        # Calculate trends (comparing with previous periods for basic trends)
        # For now, we'll use placeholder trends - in a real app, you'd calculate actual changes
        
        return Response({
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'total_teams': total_teams,
                'active_teams': active_teams,
                'total_managers': total_managers,
                'active_managers': active_managers,
                'avg_hours_per_week': avg_hours_per_week
            },
            'recent_activities': recent_activities,
            'meta': {
                'generated_at': now.isoformat(),
                'period_start': week_ago.isoformat(),
                'period_end': today.isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching dashboard stats: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'Failed to fetch dashboard statistics.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def format_time_ago(dt):
    """
    Helper function to format datetime as time ago string
    """
    from django.utils import timezone
    
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_swap_requests_view(request):
    """
    API view to get all swap requests for admin to review
    """
    # Check if user is manager and active
    if not request.user.is_manager or not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Access denied. Manager permissions required.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 50)  # Limit to max 50 per page
    
    # Get all pending swap requests across all teams
    swap_requests = SwapRequest.objects.filter(
        accepted=False,
        rejected=False
    ).select_related(
        'from_slot', 'from_slot__team', 'from_slot__assigned_member',
        'to_slot', 'to_slot__team', 'to_slot__assigned_member'
    ).order_by('-created_at')
    
    # Apply pagination
    paginator = Paginator(swap_requests, page_size)
    swap_requests_page = paginator.get_page(page)
    
    swap_requests_data = []
    for swap_request in swap_requests_page:
        swap_requests_data.append({
            'id': swap_request.id,
            'from_member': {
                'id': swap_request.from_member.id,
                'name': swap_request.from_member.name,
                'email': swap_request.from_member.email
            },
            'to_member': {
                'id': swap_request.to_member.id,
                'name': swap_request.to_member.name,
                'email': swap_request.to_member.email
            },
            'from_slot': {
                'id': swap_request.from_slot.id,
                'team_name': swap_request.from_slot.team.name,
                'start_time': swap_request.from_slot.start_time.isoformat(),
                'end_time': swap_request.from_slot.end_time.isoformat(),
                'date': swap_request.from_slot.date.isoformat(),
            },
            'to_slot': {
                'id': swap_request.to_slot.id,
                'team_name': swap_request.to_slot.team.name,
                'start_time': swap_request.to_slot.start_time.isoformat(),
                'end_time': swap_request.to_slot.end_time.isoformat(),
                'date': swap_request.to_slot.date.isoformat(),
            },
            'created_at': swap_request.created_at.isoformat()
        })
    
    return Response({
        'swap_requests': swap_requests_data,
        'pagination': {
            'current_page': swap_requests_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': swap_requests_page.has_next(),
            'has_previous': swap_requests_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_reject_swap_request_view(request, swap_request_id):
    """
    API view for admin to reject a swap request
    """
    # Check if user is manager and active
    if not request.user.is_manager or not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Access denied. Manager permissions required.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        swap_request = SwapRequest.objects.get(id=swap_request_id)
    except SwapRequest.DoesNotExist:
        return Response(
            {'error': {'commonError': 'Swap request not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if already processed
    if swap_request.accepted or swap_request.rejected:
        return Response(
            {'error': {'commonError': 'This swap request has already been processed.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Admin can only reject, not approve swap requests
    swap_request.rejected = True
    swap_request.save()
    
    return Response({
        'message': 'Swap request has been rejected.',
        'swap_request_id': swap_request.id
    }, status=status.HTTP_200_OK)