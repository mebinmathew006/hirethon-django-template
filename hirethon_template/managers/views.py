

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError

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
    
    # Extract data from request
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirmPassword')
    is_manager = request.data.get('is_manager', False)
    skills = request.data.get('skills', [])
    max_hours_per_day = request.data.get('max_hours_per_day', 8.0)
    max_hours_per_week = request.data.get('max_hours_per_week', 40.0)
    min_rest_hours = request.data.get('min_rest_hours', 8.0)
    
    # Validate required fields
    if not name or not email or not password:
        return Response(
            {'error': {'commonError': 'Name, email, and password are required.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password confirmation
    if password != confirm_password:
        return Response(
            {'error': {'confirmPassword': 'Passwords do not match.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': {'email': 'User with this email already exists.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create new user
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            is_manager=is_manager,
            skills=skills if isinstance(skills, list) else [],
            max_hours_per_day=float(max_hours_per_day),
            max_hours_per_week=float(max_hours_per_week),
            min_rest_hours=float(min_rest_hours),
        )
        
        # Prepare response data
        user_data = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'is_active': user.is_active,
            'is_manager': user.is_manager,
            'skills': user.skills,
            'max_hours_per_day': user.max_hours_per_day,
            'max_hours_per_week': user.max_hours_per_week,
            'min_rest_hours': user.min_rest_hours,
            'date_joined': user.date_joined.isoformat(),
        }
        
        return Response({
            'message': 'User created successfully.',
            'user': user_data
        }, status=status.HTTP_201_CREATED)
        
    except IntegrityError as e:
        return Response(
            {'error': {'commonError': 'User creation failed due to database constraints.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': {'commonError': 'An unexpected error occurred while creating the user.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
