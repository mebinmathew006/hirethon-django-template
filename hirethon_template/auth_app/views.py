from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings
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
    
    user = authenticate(request=request, email=email, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid email or password.'},
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
        'is_active': user.is_active,
        'is_manager': user.is_manager,
    }
    
    # Create response with user data and access token
    response = Response({
        'user': user_data,
        'access_token': str(access_token),
    }, status=status.HTTP_200_OK)
    
    refresh_token_max_age = 7 * 24 * 60 * 60  
    
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        max_age=refresh_token_max_age,
        httponly=True,  # Prevent XSS attacks
        secure=getattr(settings, 'JWT_AUTH_SECURE', False),  
        samesite=getattr(settings, 'JWT_AUTH_SAMESITE', 'Lax'),
        domain=getattr(settings, 'JWT_AUTH_COOKIE_DOMAIN', None)
    )
    
    return response
