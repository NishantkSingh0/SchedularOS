from rest_framework import serializers
from proposals.models import Proposal, Approval


class ApprovalSerializer(serializers.ModelSerializer):
    decided_by = serializers.StringRelatedField()
    
    class Meta:
        model = Approval
        fields = ['id', 'decided_by', 'decision', 'note', 'edited_payload', 'created_at']
        read_only_fields = ['id', 'decided_by', 'created_at']


class ProposalSerializer(serializers.ModelSerializer):
    approval = ApprovalSerializer(read_only=True)
    
    class Meta:
        model = Proposal
        fields = [
            'id', 'step', 'action_type', 'payload', 'rationale', 'evidence',
            'risk_tier', 'status', 'expires_at', 'executed_at', 'error_message',
            'approval', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'executed_at']


class ProposalDecideSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approved', 'rejected', 'edited'])
    note = serializers.CharField(required=False, allow_blank=True)
    edited_payload = serializers.JSONField(required=False)
