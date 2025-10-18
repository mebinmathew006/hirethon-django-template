from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

from .models import Team, TeamMember
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