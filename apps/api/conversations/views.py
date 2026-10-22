from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Conversation, Message


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only conversation inbox (inbound messages live here)"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(org=self.request.org).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        convs = self.get_queryset().select_related('lead')[:100]
        data = []
        for c in convs:
            last = c.messages.order_by('-created_at').first()
            data.append({
                "id": c.id,
                "lead": {"id": c.lead.id, "name": c.lead.name, "stage": c.lead.stage},
                "channel": c.channel,
                "status": c.status,
                "last_message": {"body": last.body, "direction": last.direction,
                                 "created_at": last.created_at.isoformat()} if last else None,
                "created_at": c.created_at.isoformat(),
            })
        return Response(data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conv = self.get_object()
        msgs = conv.messages.order_by('created_at')
        return Response([{
            "id": m.id, "direction": m.direction, "body": m.body,
            "created_at": m.created_at.isoformat(),
        } for m in msgs])
