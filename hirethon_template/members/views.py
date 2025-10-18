from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from datetime import datetime, date

from .serializers import UserDashboardSerializer
from hirethon_template.managers.models import Team, Slot, Availability, TeamMember, SwapRequest, LeaveRequest

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_schedule_view(request):
    """
    API view to get user's schedule data for calendar view
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get user's teams
    user_teams = Team.objects.filter(
        members__user=request.user, 
        members__is_active=True
    ).distinct()
    
    if not user_teams.exists():
        return Response({
            'teams': [],
            'slots': [],
            'availability': []
        }, status=status.HTTP_200_OK)
    
    # Get slots for user's teams
    slots = Slot.objects.filter(
        team__in=user_teams
    ).select_related('team', 'assigned_member').order_by('start_time')
    
    # Get user's availability
    availability = Availability.objects.filter(
        user=request.user
    ).order_by('date')
    
    # Serialize data
    schedule_data = {
        'teams': [
            {
                'id': team.id,
                'name': team.name,
                'slot_duration': str(team.slot_duration)
            }
            for team in user_teams
        ],
        'slots': [
            {
                'id': slot.id,
                'team_id': slot.team.id,
                'team_name': slot.team.name,
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'date': slot.date.isoformat(),
                'assigned_member': {
                    'id': slot.assigned_member.id,
                    'name': slot.assigned_member.name,
                    'email': slot.assigned_member.email
                } if slot.assigned_member else None,
                'is_covered': slot.is_covered,
                'is_holiday': slot.is_holiday,
                'is_mine': slot.assigned_member == request.user if slot.assigned_member else False
            }
            for slot in slots
        ],
        'availability': [
            {
                'id': avail.id,
                'date': avail.date.isoformat(),
                'is_available': avail.is_available,
                'reason': avail.reason
            }
            for avail in availability
        ]
    }
    
    return Response(schedule_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_day_slots_view(request, year, month, day):
    """
    API view to get slots for a specific date
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        target_date = date(int(year), int(month), int(day))
    except ValueError:
        return Response(
            {'error': {'commonError': 'Invalid date provided.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get user's teams
    user_teams = Team.objects.filter(
        members__user=request.user, 
        members__is_active=True
    ).distinct()
    
    if not user_teams.exists():
        return Response({
            'date': target_date.isoformat(),
            'slots': [],
            'team_members': []
        }, status=status.HTTP_200_OK)
    
    # Get slots for the specific date
    slots = Slot.objects.filter(
        team__in=user_teams,
        start_time__date=target_date
    ).select_related('team', 'assigned_member').order_by('start_time')
    
    # Get all team members for swap requests
    team_members = User.objects.filter(
        team_memberships__team__in=user_teams,
        team_memberships__is_active=True,
        is_active=True
    ).exclude(id=request.user.id).distinct().values('id', 'name', 'email')
    
    # Get user's availability for this date
    try:
        user_availability = Availability.objects.get(user=request.user, date=target_date)
        user_available = user_availability.is_available
        availability_reason = user_availability.reason
    except Availability.DoesNotExist:
        user_available = True  # Default to available
        availability_reason = ''
    
    day_data = {
        'date': target_date.isoformat(),
        'user_available': user_available,
        'availability_reason': availability_reason,
        'slots': [
            {
                'id': slot.id,
                'team_id': slot.team.id,
                'team_name': slot.team.name,
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'assigned_member': {
                    'id': slot.assigned_member.id,
                    'name': slot.assigned_member.name,
                    'email': slot.assigned_member.email
                } if slot.assigned_member else None,
                'is_covered': slot.is_covered,
                'is_holiday': slot.is_holiday,
                'is_mine': slot.assigned_member == request.user if slot.assigned_member else False
            }
            for slot in slots
        ],
        'team_members': list(team_members)
    }
    
    return Response(day_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_leave_view(request):
    """
    API view to request leave for a specific date - now requires admin approval
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    date_str = request.data.get('date')
    reason = request.data.get('reason', 'Leave requested')
    
    if not date_str:
        return Response(
            {'error': {'commonError': 'Date is required.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        target_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
    except (ValueError, AttributeError):
        return Response(
            {'error': {'commonError': 'Invalid date format.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get user's teams
    user_teams = Team.objects.filter(
        members__user=request.user, 
        members__is_active=True
    ).distinct()
    
    if not user_teams.exists():
        return Response(
            {'error': {'commonError': 'You are not a member of any active team.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create leave requests for each team the user belongs to
    leave_requests = []
    for team in user_teams:
        # Check if leave request already exists for this user, team, and date
        existing_request = LeaveRequest.objects.filter(
            user=request.user,
            team=team,
            date=target_date
        ).first()
        
        if not existing_request:
            leave_request = LeaveRequest.objects.create(
                user=request.user,
                team=team,
                date=target_date,
                reason=reason,
                status='pending'
            )
            leave_requests.append(leave_request)
        else:
            # Update existing request if it's pending
            if existing_request.status == 'pending':
                existing_request.reason = reason
                existing_request.save()
                leave_requests.append(existing_request)
    
    if not leave_requests:
        return Response(
            {'error': {'commonError': 'You already have a pending or processed leave request for this date.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'message': 'Leave request submitted successfully. Please wait for admin approval.',
        'leave_requests': [
            {
                'id': req.id,
                'team_name': req.team.name,
                'date': req.date.isoformat(),
                'reason': req.reason,
                'status': req.status
            }
            for req in leave_requests
        ]
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_swap_view(request):
    """
    API view to request a swap for an assigned slot
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    slot_id = request.data.get('slot_id')
    to_member_id = request.data.get('to_member_id')
    
    if not slot_id or not to_member_id:
        return Response(
            {'error': {'commonError': 'Slot ID and target member ID are required.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        slot = Slot.objects.get(id=slot_id, assigned_member=request.user)
    except Slot.DoesNotExist:
        return Response(
            {'error': {'commonError': 'Slot not found or not assigned to you.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        to_member = User.objects.get(id=to_member_id)
    except User.DoesNotExist:
        return Response(
            {'error': {'commonError': 'Target member not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if target member is in the same team
    if not TeamMember.objects.filter(
        team=slot.team,
        user=to_member,
        is_active=True
    ).exists():
        return Response(
            {'error': {'commonError': 'Target member is not in the same team.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if there's already a pending swap request for this slot
    if SwapRequest.objects.filter(
        slot=slot,
        from_member=request.user,
        accepted=False,
        rejected=False
    ).exists():
        return Response(
            {'error': {'commonError': 'You already have a pending swap request for this slot.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create swap request
    swap_request = SwapRequest.objects.create(
        slot=slot,
        from_member=request.user,
        to_member=to_member
    )
    
    return Response({
        'message': 'Swap request sent successfully.',
        'swap_request': {
            'id': swap_request.id,
            'slot_id': swap_request.slot.id,
            'to_member': {
                'id': swap_request.to_member.id,
                'name': swap_request.to_member.name,
                'email': swap_request.to_member.email
            },
            'created_at': swap_request.created_at.isoformat()
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_swap_requests_view(request):
    """
    API view to get swap requests received by the user
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get swap requests where current user is the target member
    swap_requests = SwapRequest.objects.filter(
        to_member=request.user,
        accepted=False,
        rejected=False
    ).select_related('slot', 'slot__team', 'from_member').order_by('-created_at')
    
    swap_requests_data = []
    for swap_request in swap_requests:
        swap_requests_data.append({
            'id': swap_request.id,
            'slot': {
                'id': swap_request.slot.id,
                'team_name': swap_request.slot.team.name,
                'start_time': swap_request.slot.start_time.isoformat(),
                'end_time': swap_request.slot.end_time.isoformat(),
                'date': swap_request.slot.date.isoformat(),
            },
            'from_member': {
                'id': swap_request.from_member.id,
                'name': swap_request.from_member.name,
                'email': swap_request.from_member.email
            },
            'created_at': swap_request.created_at.isoformat()
        })
    
    return Response({
        'swap_requests': swap_requests_data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_swap_request_view(request, swap_request_id):
    """
    API view to approve or reject a swap request
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    action = request.data.get('action')  # 'approve' or 'reject'
    
    if action not in ['approve', 'reject']:
        return Response(
            {'error': {'commonError': 'Action must be either "approve" or "reject".'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        swap_request = SwapRequest.objects.get(
            id=swap_request_id,
            to_member=request.user,
            accepted=False,
            rejected=False
        )
    except SwapRequest.DoesNotExist:
        return Response(
            {'error': {'commonError': 'Swap request not found or already responded to.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from django.utils import timezone
        
        if action == 'approve':
            # Check if the requesting user is still available for this slot
            slot_date = swap_request.slot.date
            try:
                requester_availability = Availability.objects.get(
                    user=swap_request.from_member,
                    date=slot_date
                )
                if not requester_availability.is_available:
                    return Response(
                        {'error': {'commonError': 'Cannot approve swap: The requesting user is not available on this date.'}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Availability.DoesNotExist:
                # If no availability record, assume they're available
                pass
            
            # Approve the swap
            swap_request.accepted = True
            swap_request.responded_at = timezone.now()
            swap_request.save()
            
            # Update the slot assignment
            swap_request.slot.assigned_member = request.user
            swap_request.slot.save()
            
            # Trigger revalidation after swap to ensure constraints are still met
            try:
                from hirethon_template.managers.tasks import revalidate_slot_assignments_task
                revalidate_slot_assignments_task.delay(team_id=swap_request.slot.team.id, days_back=7)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not trigger slot revalidation after swap: {e}")
            
            return Response({
                'message': 'Swap request approved successfully.',
                'swap_request': {
                    'id': swap_request.id,
                    'action': 'approved',
                    'responded_at': swap_request.responded_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        else:  # reject
            swap_request.rejected = True
            swap_request.responded_at = timezone.now()
            swap_request.save()
            
            return Response({
                'message': 'Swap request rejected successfully.',
                'swap_request': {
                    'id': swap_request.id,
                    'action': 'rejected',
                    'responded_at': swap_request.responded_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error responding to swap request: {str(e)}")
        return Response(
            {'error': {'commonError': 'An error occurred while processing the swap request.'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
