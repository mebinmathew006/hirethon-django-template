from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator
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
            'available_slots_for_swap': [],
            'user_available': True,
            'availability_reason': ''
        }, status=status.HTTP_200_OK)
    
    # Get slots for the specific date
    slots = Slot.objects.filter(
        team__in=user_teams,
        start_time__date=target_date
    ).select_related('team', 'assigned_member').order_by('start_time')
    
    # Get user's availability for this date
    try:
        user_availability = Availability.objects.get(user=request.user, date=target_date)
        user_available = user_availability.is_available
        availability_reason = user_availability.reason
    except Availability.DoesNotExist:
        user_available = True  # Default to available
        availability_reason = ''
    
    # Get available slots for swap
    # Check if we need to filter by specific team (for swap requests)
    swap_team_id = request.GET.get('for_team_id')
    current_time_filter = request.GET.get('after_current_time', 'false').lower() == 'true'
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Swap request - Team ID: {swap_team_id}, Time filter: {current_time_filter}, Target date: {target_date}")
    
    # Filter available slots for swap from the existing slots
    available_slots_for_swap = []
    from django.utils import timezone
    
    for slot in slots:
        # Skip unassigned slots
        if not slot.assigned_member:
            continue
            
        # Skip user's own slots
        if slot.assigned_member == request.user:
            continue
            
        # If requesting for a specific team, only include slots from that team
        if swap_team_id and str(slot.team.id) != swap_team_id:
            continue
            
        # If we need to filter by current time, only show future slots
        if current_time_filter:
            now = timezone.now()
            # For swap requests, only apply time filter if the target date is today
            if target_date.date() == now.date():
                # Same day - only show slots after current time
                if slot.start_time <= now:
                    continue
            # Future date - show all slots (no time filter)
        
        # Add this slot to available slots for swap
        available_slots_for_swap.append(slot)
    
    logger.info(f"Found {len(available_slots_for_swap)} available slots for swap")
    
    # Build the available slots for swap data
    available_slots_data = []
    for slot in available_slots_for_swap:
        slot_data = {
            'id': slot.id,
            'team_id': slot.team.id,
            'team_name': slot.team.name,
            'start_time': slot.start_time.isoformat(),
            'end_time': slot.end_time.isoformat(),
            'assigned_member': {
                'id': slot.assigned_member.id,
                'name': slot.assigned_member.name,
                'email': slot.assigned_member.email
            },
            'is_covered': slot.is_covered,
            'is_holiday': slot.is_holiday
        }
        available_slots_data.append(slot_data)
    
    logger.info(f"Built {len(available_slots_data)} slots for available_slots_for_swap")
    
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
        'available_slots_for_swap': available_slots_data
    }
    
    logger.info(f"Response includes available_slots_for_swap: {'available_slots_for_swap' in day_data}")
    
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
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Swap request received - Raw request.data: {request.data}")
    
    from_slot_id = request.data.get('from_slot_id')
    to_slot_id = request.data.get('to_slot_id')
    
    logger.info(f"Extracted from_slot_id: {from_slot_id}, to_slot_id: {to_slot_id}")
    
    if not from_slot_id or not to_slot_id:
        logger.warning(f"Missing required parameters - from_slot_id: {from_slot_id}, to_slot_id: {to_slot_id}")
        return Response(
            {'error': {'commonError': 'From slot ID and to slot ID are required.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from_slot = Slot.objects.get(id=from_slot_id, assigned_member=request.user)
    except Slot.DoesNotExist:
        return Response(
            {'error': {'commonError': 'From slot not found or not assigned to you.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        to_slot = Slot.objects.get(id=to_slot_id)
    except Slot.DoesNotExist:
        return Response(
            {'error': {'commonError': 'To slot not found.'}},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if both slots are from the same team
    if from_slot.team != to_slot.team:
        return Response(
            {'error': {'commonError': 'Both slots must be from the same team.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if to_slot is assigned to someone else
    if not to_slot.assigned_member:
        return Response(
            {'error': {'commonError': 'Cannot swap with an unassigned slot.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if to_slot.assigned_member == request.user:
        return Response(
            {'error': {'commonError': 'Cannot swap with your own slot.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if both slots are on the same date
    if from_slot.date != to_slot.date:
        return Response(
            {'error': {'commonError': 'Both slots must be on the same date.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if there's already a pending swap request for this combination
    if SwapRequest.objects.filter(
        from_slot=from_slot,
        to_slot=to_slot,
        accepted=False,
        rejected=False
    ).exists():
        return Response(
            {'error': {'commonError': 'You already have a pending swap request for these slots.'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create swap request
    swap_request = SwapRequest.objects.create(
        from_slot=from_slot,
        to_slot=to_slot
    )
    
    return Response({
        'message': 'Swap request sent successfully.',
        'swap_request': {
            'id': swap_request.id,
            'from_slot': {
                'id': swap_request.from_slot.id,
                'start_time': swap_request.from_slot.start_time.isoformat(),
                'end_time': swap_request.from_slot.end_time.isoformat(),
                'team_name': swap_request.from_slot.team.name
            },
            'to_slot': {
                'id': swap_request.to_slot.id,
                'start_time': swap_request.to_slot.start_time.isoformat(),
                'end_time': swap_request.to_slot.end_time.isoformat(),
                'team_name': swap_request.to_slot.team.name,
                'assigned_member': {
                    'id': swap_request.to_slot.assigned_member.id,
                    'name': swap_request.to_slot.assigned_member.name,
                    'email': swap_request.to_slot.assigned_member.email
                }
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
    
    # Get swap requests where current user is assigned to the to_slot
    swap_requests = SwapRequest.objects.filter(
        to_slot__assigned_member=request.user,
        accepted=False,
        rejected=False
    ).select_related('from_slot', 'from_slot__team', 'from_slot__assigned_member', 'to_slot', 'to_slot__team', 'to_slot__assigned_member').order_by('-created_at')
    
    swap_requests_data = []
    for swap_request in swap_requests:
        swap_requests_data.append({
            'id': swap_request.id,
            'slot': {  # This is the slot the user wants to swap WITH (from_slot)
                'id': swap_request.from_slot.id,
                'team_name': swap_request.from_slot.team.name,
                'start_time': swap_request.from_slot.start_time.isoformat(),
                'end_time': swap_request.from_slot.end_time.isoformat(),
                'date': swap_request.from_slot.date.isoformat(),
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
            to_slot__assigned_member=request.user,
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
            # Check if the requesting user is still available for the to_slot date
            slot_date = swap_request.to_slot.date
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
            
            # Approve the swap - perform the actual slot exchange
            swap_request.accepted = True
            swap_request.responded_at = timezone.now()
            swap_request.save()
            
            # Perform the swap: exchange assigned members between the slots
            from_slot_original_member = swap_request.from_slot.assigned_member
            to_slot_original_member = swap_request.to_slot.assigned_member
            
            # Update the slot assignments
            swap_request.from_slot.assigned_member = to_slot_original_member
            swap_request.to_slot.assigned_member = from_slot_original_member
            
            swap_request.from_slot.save()
            swap_request.to_slot.save()
            
            # Note: We don't trigger revalidation after manual swaps as the user's choice should be respected
            # The swap itself should maintain the existing slot structure, just changing assigned members
            
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_teams_oncall_view(request):
    """
    API view to get user's teams with current on-call person for each team
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get user's teams
    user_teams = Team.objects.filter(
        members__user=request.user, 
        members__is_active=True,
        is_active=True
    ).distinct()
    
    if not user_teams.exists():
        return Response({
            'teams': [],
            'message': 'You are not a member of any active teams.'
        }, status=status.HTTP_200_OK)
    
    from django.utils import timezone
    
    teams_data = []
    current_time = timezone.now()
    
    for team in user_teams:
        # Find current on-call person for this team
        current_slot = Slot.objects.filter(
            team=team,
            start_time__lte=current_time,
            end_time__gte=current_time,
            assigned_member__isnull=False
        ).select_related('assigned_member').first()
        
        # Get next upcoming slots for this team (next 3 slots)
        upcoming_slots = Slot.objects.filter(
            team=team,
            start_time__gt=current_time,
            assigned_member__isnull=False
        ).select_related('assigned_member').order_by('start_time')[:3]
        
        # Get team member count
        member_count = team.members.filter(is_active=True).count()
        
        team_data = {
            'id': team.id,
            'name': team.name,
            'member_count': member_count,
            'current_oncall': {
                'user_id': current_slot.assigned_member.id,
                'name': current_slot.assigned_member.name,
                'email': current_slot.assigned_member.email,
                'start_time': current_slot.start_time.isoformat(),
                'end_time': current_slot.end_time.isoformat()
            } if current_slot else None,
            'upcoming_slots': [
                {
                    'user_id': slot.assigned_member.id,
                    'name': slot.assigned_member.name,
                    'email': slot.assigned_member.email,
                    'start_time': slot.start_time.isoformat(),
                    'end_time': slot.end_time.isoformat(),
                    'date': slot.date.isoformat()
                }
                for slot in upcoming_slots
            ],
            'team_schedule_constraints': {
                'max_hours_per_day': team.max_hours_per_day,
                'max_hours_per_week': team.max_hours_per_week,
                'min_rest_hours': team.min_rest_hours
            }
        }
        
        teams_data.append(team_data)
    
    return Response({
        'teams': teams_data,
        'current_time': current_time.isoformat(),
        'user_id': request.user.id
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_teams_oncall_view(request):
    """
    API view to get ALL teams with current on-call person for each team (not just user's teams)
    """
    if not request.user.is_active:
        return Response(
            {'error': {'commonError': 'Your account has been deactivated. Please contact an administrator.'}},
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
    
    # Get ALL active teams (not just user's teams)
    teams_queryset = Team.objects.filter(is_active=True).order_by('name')
    
    if not teams_queryset.exists():
        return Response({
            'teams': [],
            'message': 'No active teams found.',
            'pagination': {
                'current_page': 1,
                'total_pages': 0,
                'total_count': 0,
                'page_size': page_size,
                'has_next': False,
                'has_previous': False,
            }
        }, status=status.HTTP_200_OK)
    
    # Apply pagination
    paginator = Paginator(teams_queryset, page_size)
    
    try:
        teams_page = paginator.page(page)
    except:
        # If page is out of range, return the last page
        teams_page = paginator.page(paginator.num_pages)
    
    from django.utils import timezone
    
    teams_data = []
    current_time = timezone.now()
    
    for team in teams_page:
        # Find current on-call person for this team
        current_slot = Slot.objects.filter(
            team=team,
            start_time__lte=current_time,
            end_time__gte=current_time,
            assigned_member__isnull=False
        ).select_related('assigned_member').first()
        
        # Get next upcoming slots for this team (next 3 slots)
        upcoming_slots = Slot.objects.filter(
            team=team,
            start_time__gt=current_time,
            assigned_member__isnull=False
        ).select_related('assigned_member').order_by('start_time')[:3]
        
        # Get team member count
        member_count = team.members.filter(is_active=True).count()
        
        # Check if current user is a member of this team
        is_user_member = team.members.filter(user=request.user, is_active=True).exists()
        
        team_data = {
            'id': team.id,
            'name': team.name,
            'member_count': member_count,
            'is_user_member': is_user_member,
            'current_oncall': {
                'user_id': current_slot.assigned_member.id,
                'name': current_slot.assigned_member.name,
                'email': current_slot.assigned_member.email,
                'start_time': current_slot.start_time.isoformat(),
                'end_time': current_slot.end_time.isoformat()
            } if current_slot else None,
            'upcoming_slots': [
                {
                    'user_id': slot.assigned_member.id,
                    'name': slot.assigned_member.name,
                    'email': slot.assigned_member.email,
                    'start_time': slot.start_time.isoformat(),
                    'end_time': slot.end_time.isoformat(),
                    'date': slot.date.isoformat()
                }
                for slot in upcoming_slots
            ],
            'team_schedule_constraints': {
                'max_hours_per_day': team.max_hours_per_day,
                'max_hours_per_week': team.max_hours_per_week,
                'min_rest_hours': team.min_rest_hours
            }
        }
        
        teams_data.append(team_data)
    
    return Response({
        'teams': teams_data,
        'current_time': current_time.isoformat(),
        'user_id': request.user.id,
        'pagination': {
            'current_page': teams_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': teams_page.has_next(),
            'has_previous': teams_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)
