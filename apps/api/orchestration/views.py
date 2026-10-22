from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from orchestration.models import WorkflowRun, RunStep
from orchestration.serializers import WorkflowRunSerializer, RunStepSerializer, GoalRequestSerializer
from orchestration.tasks import create_workflow_from_goal
from orchestration.engine import cancel_workflow, pause_workflow, resume_workflow


class WorkflowRunViewSet(viewsets.ModelViewSet):
    """ViewSet for WorkflowRun model"""
    serializer_class = WorkflowRunSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        org = self.request.org
        if org:
            return WorkflowRun.objects.filter(org=org)
        return WorkflowRun.objects.none()
    
    @action(detail=False, methods=['post'])
    def launch(self, request):
        """Launch a new workflow from a natural language goal"""
        serializer = GoalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        goal = serializer.validated_data['goal']
        org_id = str(request.org.id)
        
        # Create workflow asynchronously
        task = create_workflow_from_goal.apply_async(args=(org_id, goal))
        
        return Response({
            "task_id": task.id,
            "message": "Orchestrator is planning..."
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a workflow"""
        try:
            cancel_workflow(pk)
            return Response({"status": "cancelled"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a workflow"""
        try:
            pause_workflow(pk)
            return Response({"status": "paused"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused workflow"""
        try:
            resume_workflow(pk)
            return Response({"status": "resumed"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RunStepViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for RunStep model"""
    serializer_class = RunStepSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        org = self.request.org
        if not org:
            return RunStep.objects.none()
        qs = RunStep.objects.filter(run__org=org)
        run_id = self.request.query_params.get('run')
        if run_id:
            qs = qs.filter(run_id=run_id)
        return qs.order_by('run_at', 'id')
