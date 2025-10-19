"""
Factory classes for creating test data in managers app
"""
import factory
from django.utils import timezone
from datetime import timedelta, date, time
from factory.django import DjangoModelFactory

from hirethon_template.users.tests.factories import UserFactory
from ..models import Team, TeamMember, Slot, Availability, Holiday, LeaveRequest, SwapRequest, Alert


class TeamFactory(DjangoModelFactory):
    """Factory for creating Team instances"""
    
    class Meta:
        model = Team
    
    name = factory.Sequence(lambda n: f"Team {n}")
    slot_duration = timedelta(hours=1)
    max_hours_per_day = 8.0
    max_hours_per_week = 40.0
    min_rest_hours = 8.0
    is_active = False


class TeamMemberFactory(DjangoModelFactory):
    """Factory for creating TeamMember instances"""
    
    class Meta:
        model = TeamMember
    
    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
    is_manager = False
    is_active = True


class SlotFactory(DjangoModelFactory):
    """Factory for creating Slot instances"""
    
    class Meta:
        model = Slot
    
    team = factory.SubFactory(TeamFactory)
    start_time = factory.LazyFunction(
        lambda: timezone.now().replace(
            hour=9, minute=0, second=0, microsecond=0
        )
    )
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time + obj.team.slot_duration
    )
    is_covered = False


class AvailabilityFactory(DjangoModelFactory):
    """Factory for creating Availability instances"""
    
    class Meta:
        model = Availability
    
    user = factory.SubFactory(UserFactory)
    date = factory.LazyFunction(lambda: timezone.now().date())
    is_available = True


class HolidayFactory(DjangoModelFactory):
    """Factory for creating Holiday instances"""
    
    class Meta:
        model = Holiday
    
    team = factory.SubFactory(TeamFactory)
    date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=30))
    description = factory.Faker('sentence')


class LeaveRequestFactory(DjangoModelFactory):
    """Factory for creating LeaveRequest instances"""
    
    class Meta:
        model = LeaveRequest
    
    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
    date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=1))
    reason = factory.Faker('sentence')
    status = 'pending'


class SwapRequestFactory(DjangoModelFactory):
    """Factory for creating SwapRequest instances"""
    
    class Meta:
        model = SwapRequest
    
    from_slot = factory.SubFactory(SlotFactory)
    to_slot = factory.SubFactory(SlotFactory)
    status = 'pending'
    reason = factory.Faker('sentence')


class AlertFactory(DjangoModelFactory):
    """Factory for creating Alert instances"""
    
    class Meta:
        model = Alert
    
    slot = factory.SubFactory(SlotFactory)
    team = factory.SubFactory(TeamFactory)
    message = factory.Faker('sentence')
