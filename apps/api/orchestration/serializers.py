from rest_framework import serializers
from orchestration.models import WorkflowRun, RunStep, AgentRun


class RunStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunStep
        fields = [
            'id', 'run', 'agent', 'state', 'run_at', 'started_at',
            'completed_at', 'attempt', 'input_context', 'output', 'error_message'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'attempt']


class AgentRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRun
        fields = [
            'id', 'agent', 'input_context', 'output', 'proposal_count',
            'duration_ms', 'error_message'
        ]
        read_only_fields = ['id']


class WorkflowRunSerializer(serializers.ModelSerializer):
    steps = RunStepSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkflowRun
        fields = [
            'id', 'goal', 'status', 'lead', 'brand', 'context', 'steps',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'steps']


class GoalRequestSerializer(serializers.Serializer):
    goal = serializers.CharField(max_length=1000)
