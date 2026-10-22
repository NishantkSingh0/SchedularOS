from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from proposals.models import Proposal, Approval
from proposals.serializers import ProposalSerializer, ApprovalSerializer, ProposalDecideSerializer
from proposals.tasks import execute_proposal
from core.policy import update_trust_after_decision
from django.contrib.auth.models import User


class ProposalViewSet(viewsets.ModelViewSet):
    """ViewSet for Proposal model"""
    serializer_class = ProposalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        org = self.request.org
        if org:
            queryset = Proposal.objects.filter(org=org)
            
            # Filter by status if provided
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            return queryset
        return Proposal.objects.none()
    
    @action(detail=True, methods=['post'])
    def decide(self, request, pk=None):
        """Decide on a proposal (approve/reject/edit)"""
        proposal = self.get_object()
        
        # Check if proposal is pending
        if proposal.status != 'pending':
            return Response(
                {"error": f"Proposal is {proposal.status}, cannot decide"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProposalDecideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        decision = serializer.validated_data['decision']
        note = serializer.validated_data.get('note', '')
        edited_payload = serializer.validated_data.get('edited_payload')

        # Rejection requires feedback explaining why
        if decision == 'rejected' and not note.strip():
            return Response(
                {"error": "Rejection requires a feedback note"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update proposal if edited
        if decision == 'edited' and edited_payload:
            proposal.payload = edited_payload
            proposal.save()
        
        # Update proposal status
        if decision == 'approved':
            proposal.mark_approved()
        elif decision == 'rejected':
            proposal.mark_rejected()
        elif decision == 'edited':
            proposal.mark_edited()
        
        # Create approval record
        Approval.objects.create(
            proposal=proposal,
            decided_by=request.user,
            decision=decision,
            note=note,
            edited_payload=edited_payload
        )
        
        # Create audit event
        from core.models import AuditEvent
        AuditEvent.objects.create(
            org_id=proposal.org_id,
            event_type="proposal.decided",
            proposal_id=proposal.id,
            user_id=request.user.id,
            metadata={"decision": decision}
        )
        
        # Update trust level
        update_trust_after_decision(
            org_id=str(proposal.org_id),
            agent=proposal.step.agent,
            action_type=proposal.action_type,
            decision=decision
        )
        
        # Execute if approved (rejected proposals never reach the executor)
        if decision in ['approved', 'edited']:
            execute_proposal.apply_async(queue="executor", args=(str(proposal.id),))

        # Resolve the step if no proposals remain pending
        from orchestration.engine import resolve_step_after_decisions
        resolve_step_after_decisions(str(proposal.step_id))

        # Return updated proposal
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)
