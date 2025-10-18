from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()
# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=255)
    slot_duration = models.DurationField(default=timedelta(hours=1))
    max_hours_per_day = models.FloatField(default=8)
    max_hours_per_week = models.FloatField(default=40)
    min_rest_hours = models.FloatField(default=8)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    is_manager = models.BooleanField(default=False)  # optional per team
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'team')

class Holiday(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="holidays")
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ('team', 'date')

class Availability(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="availability")
    date = models.DateField()  # The date when the user has leave/unavailability record
    is_available = models.BooleanField(default=True)  # True = available, False = unavailable (leave/PTO)
    reason = models.CharField(max_length=255, blank=True, help_text="Reason for unavailability (e.g., 'PTO', 'Sick leave')")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'date')
        verbose_name_plural = 'availabilities'
    
    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.user.name} - {self.date} ({status})"


class Slot(models.Model):
    """
    Represents an on-call shift/slot for a team
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="slots")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    assigned_member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_slots')
    is_holiday = models.BooleanField(default=False)
    is_covered = models.BooleanField(default=False, help_text="True if the slot is covered by an assigned member")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('team', 'start_time')
        ordering = ['start_time']
    
    def __str__(self):
        if self.assigned_member:
            return f"{self.team.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')} ({self.assigned_member.name})"
        return f"{self.team.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')} (Unassigned)"
    
    @property
    def date(self):
        """Get the date of this slot"""
        return self.start_time.date()
    
    @property
    def duration(self):
        """Get the duration of this slot"""
        return self.end_time - self.start_time
    
    def is_active_now(self):
        """Check if this slot is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class SwapRequest(models.Model):
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='swap_requests')
    from_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swap_requests_sent')
    to_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swap_requests_received')
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    def is_pending(self):
        return not (self.accepted or self.rejected)

        
class Alert(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='alerts')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='leave_requests')
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leave_requests')
    
    class Meta:
        unique_together = ('user', 'team', 'date')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.date} ({self.status})"
