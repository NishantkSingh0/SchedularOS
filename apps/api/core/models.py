import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from pgvector.django import VectorField


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary key"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class TimestampMixin(models.Model):
    """Mixin for created_at and updated_at timestamps"""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class OrgScopedMixin:
    """Mixin for organization-scoped models"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Organization model for multi-tenancy"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    settings = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'organizations'
    
    def __str__(self):
        return self.name


class Brand(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Brand configuration for an organization"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    voice = models.TextField()
    rules = models.JSONField(default=dict)
    colors = models.JSONField(default=dict)
    logo_url = models.URLField(blank=True)
    
    class Meta:
        db_table = 'brands'
    
    def __str__(self):
        return f"{self.org.name} - {self.name}"


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('agent', 'Agent'),
        ('viewer', 'Viewer'),
    ], default='viewer')
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.org.name}"


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Lead model for customer/prospect tracking"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    stage = models.CharField(max_length=50, choices=[
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost')
    ], default='new')
    score = models.IntegerField(default=0)
    tags = models.JSONField(default=list)
    has_whatsapp_consent = models.BooleanField(default=False)
    has_email_consent = models.BooleanField(default=False)
    opted_out_at = models.DateTimeField(null=True, blank=True)
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'leads'
    
    def __str__(self):
        return f"{self.name} ({self.stage})"


class ConsentRecord(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Append-only consent tracking"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    channel = models.CharField(max_length=50)  # whatsapp, email, sms
    consented = models.BooleanField()
    source = models.CharField(max_length=100)  # form, import, manual
    
    class Meta:
        db_table = 'consent_records'
    
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("ConsentRecord is append-only — updates forbidden.")
        super().save(*args, **kwargs)


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Conversation thread for a lead"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    channel = models.CharField(max_length=50, choices=[
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS'),
    ])
    status = models.CharField(max_length=50, default='active')
    
    class Meta:
        db_table = 'conversations'
    
    def __str__(self):
        return f"{self.lead.name} - {self.channel}"


class Message(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Message within a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    direction = models.CharField(max_length=20, choices=[
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound')
    ])
    body = models.TextField()
    is_ai_generated = models.BooleanField(default=False)
    external_id = models.CharField(max_length=255, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'messages'
    
    def __str__(self):
        return f"{self.direction}: {self.body[:50]}..."


class Budget(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Budget tracking per agent"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)
    agent = models.CharField(max_length=50)
    soft_cap = models.IntegerField()  # in paise (cents)
    hard_cap = models.IntegerField()  # in paise
    period = models.CharField(max_length=20, default='daily')
    
    class Meta:
        db_table = 'budgets'
        unique_together = [['org', 'agent', 'period']]
    
    def __str__(self):
        return f"{self.agent} - {self.period}"


class AgentTrustState(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Trust level tracking per agent per action type"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)
    agent = models.CharField(max_length=50)
    action_type = models.CharField(max_length=255)
    trust_level = models.IntegerField(default=1)  # L0-L3
    total_decisions = models.IntegerField(default=0)
    approvals = models.IntegerField(default=0)
    rejections = models.IntegerField(default=0)
    last_rejection_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'agent_trust_states'
        unique_together = [['org', 'agent', 'action_type']]
    
    def __str__(self):
        return f"{self.agent}/{self.action_type} - L{self.trust_level}"


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Knowledge base documents for RAG with pgvector support"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    embedding = VectorField(dimensions=1536, null=True)  # OpenAI embeddings are 1536 dimensions
    metadata = models.JSONField(default=dict)
    source = models.CharField(max_length=255, default="manual")
    chunk_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'knowledge_documents'
        indexes = [
            models.Index(fields=['org']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return self.title


class AuditEvent(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Append-only audit log"""
    org = models.ForeignKey('Organization', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100)
    proposal_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'audit_events'
    
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("AuditEvent is append-only — updates forbidden.")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.event_type} at {self.created_at}"
