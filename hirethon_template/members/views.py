from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import UserDashboardSerializer

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_dashboard_view(request):
    """
    API view to get user dashboard data including teams and availability
    """
    # Check if user is active
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Serialize the user data with dashboard information
    serializer = UserDashboardSerializer(request.user)
    
    return Response({
        'user': serializer.data
    }, status=status.HTTP_200_OK)
