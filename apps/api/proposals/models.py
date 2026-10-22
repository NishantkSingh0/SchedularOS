import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import UUIDPrimaryKeyMixin, TimestampMixin
from orchestration.models import RunStep


class Proposal(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Agent proposal awaiting human approval"""
    org = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    step = models.ForeignKey(RunStep, on_delete=models.CASCADE, related_name='proposals')
    action_type = models.CharField(max_length=255)
    payload = models.JSONField()
    rationale = models.TextField()
    evidence = models.JSONField(default=dict)
    risk_tier = models.IntegerField(default=2)  # T0-T3
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('edited', 'Edited'),
        ('expired', 'Expired'),
        ('executed', 'Executed'),
        ('failed', 'Failed')
    ], default='pending')
    idempotency_key = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'proposals'
    
    def __str__(self):
        return f"Proposal {self.id} - {self.action_type} ({self.status})"
    
    def mark_approved(self):
        """Mark proposal as approved"""
        self.status = 'approved'
        self.save()
    
    def mark_rejected(self):
        """Mark proposal as rejected"""
        self.status = 'rejected'
        self.save()
    
    def mark_edited(self):
        """Mark proposal as edited"""
        self.status = 'edited'
        self.save()
    
    def mark_executed(self):
        """Mark proposal as executed"""
        self.status = 'executed'
        self.executed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message: str = ""):
        """Mark proposal as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
    
    def mark_expired(self):
        """Mark proposal as expired"""
        self.status = 'expired'
        self.save()


class Approval(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Human approval record for a proposal"""
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE)
    decided_by = models.ForeignKey(User, on_delete=models.CASCADE)
    decision = models.CharField(max_length=20, choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('edited', 'Edited')
    ])
    note = models.TextField(blank=True)
    edited_payload = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'approvals'
    
    def __str__(self):
        return f"Approval {self.id} - {self.decision}"
