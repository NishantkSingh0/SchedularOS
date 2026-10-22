import uuid
from django.db import models
from django.db import transaction
from django.utils import timezone
from core.models import UUIDPrimaryKeyMixin, TimestampMixin


class WorkflowRun(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Workflow execution instance"""
    org = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    goal = models.TextField()
    status = models.CharField(max_length=50, choices=[
        ('planning', 'Planning'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused')
    ], default='planning')
    lead = models.ForeignKey('core.Lead', on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey('core.Brand', on_delete=models.SET_NULL, null=True, blank=True)
    context = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'workflow_runs'
    
    def __str__(self):
        return f"Workflow {self.id} - {self.goal[:50]}"
    
    def mark_running(self):
        """Mark workflow as running"""
        self.status = 'running'
        self.save()
    
    def mark_completed(self):
        """Mark workflow as completed"""
        self.status = 'completed'
        self.save()
    
    def mark_failed(self):
        """Mark workflow as failed"""
        self.status = 'failed'
        self.save()
    
    def mark_cancelled(self):
        """Mark workflow as cancelled"""
        self.status = 'cancelled'
        self.save()
    
    def mark_paused(self):
        """Mark workflow as paused"""
        self.status = 'paused'
        self.save()


class RunStep(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Individual step within a workflow"""
    run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name='steps')
    agent = models.CharField(max_length=50)
    state = models.CharField(max_length=50, choices=[
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('awaiting_human', 'Awaiting Human'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')
    run_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    attempt = models.IntegerField(default=0)
    idempotency_key = models.CharField(max_length=255, unique=True)
    input_context = models.JSONField(default=dict)
    output = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'run_steps'
    
    def __str__(self):
        return f"Step {self.id} - {self.agent} ({self.state})"
    
    def mark_running(self):
        """Mark step as running"""
        self.state = 'running'
        self.started_at = timezone.now()
        self.attempt += 1
        self.save()
    
    def mark_done(self):
        """Mark step as done"""
        self.state = 'done'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_awaiting_human(self):
        """Mark step as awaiting human approval"""
        self.state = 'awaiting_human'
        self.save()
    
    def mark_failed(self, error_message: str = ""):
        """Mark step as failed"""
        self.state = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def mark_cancelled(self):
        """Mark step as cancelled"""
        self.state = 'cancelled'
        self.completed_at = timezone.now()
        self.save()


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Individual agent execution record"""
    step = models.ForeignKey(RunStep, on_delete=models.CASCADE, related_name='agent_runs')
    agent = models.CharField(max_length=50)
    input_context = models.JSONField(default=dict)
    output = models.JSONField(default=dict)
    proposal_count = models.IntegerField(default=0)
    duration_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'agent_runs'
    
    def __str__(self):
        return f"AgentRun {self.id} - {self.agent}"
