from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import Team
from .views import check_user_activity

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_slots_manually_view(request):
    """
    API view to manually trigger slot creation for the next 7 days
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can create slots.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from datetime import date, timedelta
        from django.utils import timezone
        from .tasks import create_slots_daily_task
        
        # Get parameters
        team_id = request.data.get('team_id')
        days_ahead = request.data.get('days_ahead', 7)
        
        # Validate days_ahead
        if not isinstance(days_ahead, int) or days_ahead < 1 or days_ahead > 30:
            return Response(
                {'error': {'commonError': 'days_ahead must be an integer between 1 and 30'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate date range
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days_ahead - 1)
        
        # Get team if specified
        team = None
        if team_id:
            try:
                team = Team.objects.get(id=team_id, is_active=True)
            except Team.DoesNotExist:
                return Response(
                    {'error': {'commonError': 'Team not found or inactive.'}},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Trigger the task
        task = create_slots_daily_task.delay()
        
        return Response({
            'message': f'Slot creation task started for {"team " + team.name if team else "all teams"}.',
            'task_id': task.id,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in manual slot creation: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'An error occurred while starting slot creation.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revalidate_slots_view(request):
    """
    API view to manually trigger slot revalidation
    """
    if not request.user.is_manager:
        return Response(
            {'error': {'commonError': 'Only managers can revalidate slots.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    activity_check = check_user_activity(request.user)
    if activity_check:
        return activity_check
    
    try:
        from .tasks import revalidate_slot_assignments_task
        
        # Get parameters
        team_id = request.data.get('team_id')
        days_back = request.data.get('days_back', 7)
        
        # Validate days_back
        if not isinstance(days_back, int) or days_back < 1 or days_back > 30:
            return Response(
                {'error': {'commonError': 'days_back must be an integer between 1 and 30'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate team if specified
        if team_id:
            try:
                team = Team.objects.get(id=team_id, is_active=True)
            except Team.DoesNotExist:
                return Response(
                    {'error': {'commonError': 'Team not found or inactive.'}},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Trigger the revalidation task
        task = revalidate_slot_assignments_task.delay(team_id=team_id, days_back=days_back)
        
        return Response({
            'message': f'Slot revalidation task started for {"team " + team.name if team_id else "all teams"}.',
            'task_id': task.id,
            'parameters': {
                'team_id': team_id,
                'days_back': days_back
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in slot revalidation: {str(e)}", exc_info=True)
        return Response(
            {'error': {'commonError': 'An error occurred while starting slot revalidation.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
