from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)

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
        'access_token': str(access_token),
    }
    
    # Create response with user data and access token
    response = Response({
        'user': user_data
        
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


class TokenRefreshFromCookieView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Extract the refresh token from cookies
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(
                {"detail": "Refresh token not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create a RefreshToken instance and generate a new access token
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            # Get user ID from refresh token payload
            user_id = refresh.payload['user_id']
           
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # Create response with access token and user details in body
            response = Response({
                    'access_token': access_token,
            }, status=status.HTTP_200_OK)
            return response
        except TokenError as e:
            return Response(
                {"detail": f"Invalid or expired refresh token.{e}"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
