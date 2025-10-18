from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    API view for user login
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': {'email': ['This field is required.'], 'password': ['This field is required.']}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate user
    user = authenticate(request=request, email=email, password=password)
    
    if not user:
        return Response(
            {'error': {'commonError': 'Invalid email or password.'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': {'commonError': 'Account is deactivated.'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    # Prepare user data for frontend
    user_data = {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
        'role': user.role,
        'is_manager': user.is_manager,
        'skills': user.skills,
        'max_hours_per_day': user.max_hours_per_day,
        'max_hours_per_week': user.max_hours_per_week,
        'min_rest_hours': user.min_rest_hours,
        'date_joined': user.date_joined.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }
    
    return Response({
        'user': user_data,
        'access_token': str(access_token),
        'refresh_token': str(refresh)
    }, status=status.HTTP_200_OK)
