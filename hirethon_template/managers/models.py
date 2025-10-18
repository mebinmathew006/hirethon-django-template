from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=255)
    slot_duration = models.DurationField(default=3600) 
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
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_hard_block = models.BooleanField(default=True)  # True = PTO / unavailability, False = soft preference


class Slot(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="slots")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    assigned_member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_slots')
    is_holiday = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('team', 'start_time')

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
