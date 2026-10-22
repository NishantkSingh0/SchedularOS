"""
Task-oriented API facade.

Each endpoint maps a typed, per-task request onto a canonical proposal and
hands it to `submit_proposal` — the SAME 8-step policy gate every agent
proposal goes through. Nothing here calls a connector directly:

    typed request -> build proposal -> submit_proposal -> policy gate
        -> (auto) execute_proposal | (human) pending for /proposals/decide

Consent, budget caps, risk tiers, trust levels and audit trails are all
unchanged — the facade only supplies a typed input contract.
"""
import uuid
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# task -> owning agent (used for budget caps and trust attribution)
TASK_AGENT = {
    'lead.score': 'lead_generation',
    'lead.tag': 'lead_generation',
    'lead.assign': 'lead_generation',
    'whatsapp.send_message': 'conversation',
    'email.send': 'followup',
    'followup.schedule': 'followup',
    'meta.create_campaign': 'paid_media',
    'meta.update_campaign': 'paid_media',
    'google.create_campaign': 'paid_media',
    'content.generate_social_post': 'creative',
    'content.generate_ad_copy': 'creative',
    'content.generate_image': 'creative',
    'content.generate_landing_page': 'creative',
}

# action_type domain -> owning agent (fallback when no exact match)
DOMAIN_AGENT = {
    'lead': 'lead_generation',
    'research': 'research',
    'whatsapp': 'conversation',
    'email': 'followup',
    'followup': 'followup',
    'meta': 'paid_media',
    'google': 'paid_media',
    'budget': 'paid_media',
    'content': 'creative',
    'web': 'research',
    'conversation': 'conversation',
    'conversion': 'conversion',
    'customer': 'customer_success',
}


def _task_step(org, agent: str, goal: str, lead=None):
    """Create an API-sourced run + step to carry the proposal.

    The step is NOT dispatched to an agent — the API call itself is the
    proposal source. State starts awaiting_human; resolve_step_after_decisions
    settles it after the human decision (or immediately if auto-approved).
    """
    from orchestration.models import WorkflowRun, RunStep

    run = WorkflowRun.objects.create(
        org=org, goal=goal, lead=lead,
        status='running', context={'source': 'tasks_api'},
    )
    return RunStep.objects.create(
        run=run, agent=agent, state='awaiting_human',
        run_at=__import__('django.utils.timezone', fromlist=['now']).now(),
        idempotency_key=f"task:{uuid.uuid4()}",
    )


def _submit(request, action_type: str, payload: dict, rationale: str,
            risk_tier: int, lead=None, evidence: dict = None, goal: str = None):
    """Build the canonical proposal and push it through the policy gate."""
    import redis
    from django.conf import settings
    from core.policy import submit_proposal
    from orchestration.engine import resolve_step_after_decisions

    agent = TASK_AGENT.get(action_type, DOMAIN_AGENT.get(action_type.split('.')[0], 'orchestrator'))
    step = _task_step(request.org, agent, goal or f"{action_type} via API", lead=lead)
    rc = redis.from_url(settings.REDIS_URL)

    result = submit_proposal(str(request.org.id), step, {
        "action_type": action_type,
        "payload": payload,
        "rationale": rationale,
        "evidence": evidence or {"source": "api", "user": request.user.username},
        "risk_tier": risk_tier,
    }, redis_client=rc)

    if result.get('needs_human'):
        return Response({
            "proposal_id": result["proposal_id"],
            "status": "pending",
            "step_id": str(step.id),
            "detail": "Requires human approval — see Approval Center",
        }, status=status.HTTP_202_ACCEPTED)

    # auto-approved (or executed) — settle the carrier step immediately
    resolve_step_after_decisions(str(step.id))
    return Response({
        "proposal_id": result.get("proposal_id"),
        "status": "auto_approved",
        "blocked": result.get("blocked", False),
        "reason": result.get("reason"),
        "step_id": str(step.id),
    }, status=status.HTTP_200_OK)


# ---------------- input serializers ----------------

class ScoreSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=100)
    rationale = serializers.CharField(required=False, allow_blank=True)

class TagSerializer(serializers.Serializer):
    tags = serializers.ListField(child=serializers.CharField(), min_length=1)

class ReplySerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=4096)
    rationale = serializers.CharField(required=False, allow_blank=True)

class CampaignSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1)
    objective = serializers.ChoiceField(choices=[
        'LINK_CLICKS', 'CONVERSIONS', 'REACH', 'BRAND_AWARENESS', 'LEAD_GENERATION',
        'TRAFFIC', 'SALES', 'AWARENESS'])
    daily_budget_paise = serializers.IntegerField(min_value=100)
    platform = serializers.ChoiceField(choices=['meta', 'google'], default='meta')
    target_audience = serializers.DictField(required=False)
    rationale = serializers.CharField(required=False, allow_blank=True)

class CampaignStatusSerializer(serializers.Serializer):
    campaign_id = serializers.CharField()
    status = serializers.ChoiceField(choices=['ACTIVE', 'PAUSED'])

class FollowUpSerializer(serializers.Serializer):
    lead_id = serializers.IntegerField()
    channel = serializers.ChoiceField(choices=['whatsapp', 'email'])
    message = serializers.CharField(min_length=1)
    delay_minutes = serializers.IntegerField(min_value=0, default=60)

class CreativeSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=['social_post', 'ad_copy', 'image', 'landing_page'])
    brief = serializers.CharField(min_length=1)
    platform = serializers.CharField(required=False, allow_blank=True)
    count = serializers.IntegerField(min_value=1, max_value=10, default=1)

class LaunchSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1)
    objective = serializers.CharField()
    total_budget_paise = serializers.IntegerField(min_value=1000)
    platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=['meta', 'google']), min_length=1)


class TaskViewSet(viewsets.ViewSet):
    """Task-oriented facade — every action ends at submit_proposal, never a connector."""
    permission_classes = [IsAuthenticated]

    # ---------- Leads ----------
    @action(detail=False, methods=['post'], url_path='leads/(?P<lead_id>[^/.]+)/score')
    def score_lead(self, request, lead_id=None):
        """Score a lead. Internal T0 action — usually auto-executes."""
        s = ScoreSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        from core.models import Lead
        lead = Lead.objects.filter(id=lead_id, org=request.org).first()
        if not lead:
            return Response({"error": "lead not found"}, status=404)
        return _submit(request, 'lead.score',
                       {"lead_id": lead.id, "score": s.validated_data['score']},
                       s.validated_data.get('rationale') or 'Manual score update',
                       risk_tier=0, lead=lead)

    @action(detail=False, methods=['post'], url_path='leads/(?P<lead_id>[^/.]+)/tag')
    def tag_lead(self, request, lead_id=None):
        """Tag a lead. Internal T0 action — usually auto-executes."""
        s = TagSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        from core.models import Lead
        lead = Lead.objects.filter(id=lead_id, org=request.org).first()
        if not lead:
            return Response({"error": "lead not found"}, status=404)
        return _submit(request, 'lead.tag',
                       {"lead_id": lead.id, "tags": s.validated_data['tags']},
                       'Manual tag update', risk_tier=0, lead=lead)

    # ---------- Conversations ----------
    @action(detail=False, methods=['post'], url_path='conversations/(?P<conv_id>[^/.]+)/reply')
    def reply(self, request, conv_id=None):
        """Send a WhatsApp reply — consent-gated (blocked if lead hasn't consented)."""
        s = ReplySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        from core.models import Conversation
        conv = Conversation.objects.filter(id=conv_id, org=request.org).select_related('lead').first()
        if not conv:
            return Response({"error": "conversation not found"}, status=404)
        return _submit(request, 'whatsapp.send_message',
                       {"to": conv.lead.phone, "body": s.validated_data['body'],
                        "conversation_id": conv.id},
                       s.validated_data.get('rationale') or 'Manual reply',
                       risk_tier=2, lead=conv.lead,
                       evidence={"conversation_id": conv.id, "channel": conv.channel})

    # ---------- Advertising ----------
    @action(detail=False, methods=['post'], url_path='advertising/campaigns')
    def create_campaign(self, request):
        """Create an ad campaign — spend-bearing, elevated to human review."""
        s = CampaignSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        action_type = f"{d['platform']}.create_campaign"
        return _submit(request, action_type, {
            "name": d['name'], "objective": d['objective'],
            "daily_budget": d['daily_budget_paise'] / 100,
            "spend_paise": d['daily_budget_paise'],
            "target_audience": d.get('target_audience', {}),
        }, d.get('rationale') or f"Launch {d['platform']} campaign {d['name']}",
            risk_tier=3,
            evidence={"source": "api", "platform": d['platform']})

    @action(detail=False, methods=['post'], url_path='advertising/campaign-status')
    def campaign_status(self, request):
        """Pause/activate a campaign — T1, auto at trust L2+."""
        s = CampaignStatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        return _submit(request, 'meta.update_campaign',
                       {"campaign_id": d['campaign_id'], "status": d['status']},
                       f"Set campaign {d['campaign_id']} to {d['status']}", risk_tier=1)

    # ---------- Follow-ups ----------
    @action(detail=False, methods=['post'], url_path='followups/schedule')
    def schedule_followup(self, request):
        """Schedule a follow-up — consent-gated by channel."""
        s = FollowUpSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        from core.models import Lead
        lead = Lead.objects.filter(id=d['lead_id'], org=request.org).first()
        if not lead:
            return Response({"error": "lead not found"}, status=404)
        action = 'whatsapp.send_message' if d['channel'] == 'whatsapp' else 'email.send'
        payload = {"lead_id": lead.id, "delay_minutes": d['delay_minutes'],
                   "scheduled": True}
        if d['channel'] == 'whatsapp':
            payload.update({"to": lead.phone, "body": d['message']})
        else:
            payload.update({"to": lead.email, "subject": "Following up", "body": d['message']})
        return _submit(request, action, payload,
                       f"Scheduled {d['channel']} follow-up in {d['delay_minutes']}m",
                       risk_tier=2, lead=lead,
                       evidence={"scheduled": True, "delay_minutes": d['delay_minutes']})

    # ---------- Creative ----------
    @action(detail=False, methods=['post'], url_path='creative/generate')
    def generate_creative(self, request):
        """Generate a creative artifact — T1 proposal."""
        s = CreativeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        action_type = f"content.generate_{d['kind']}"
        return _submit(request, action_type, {
            "brief": d['brief'], "platform": d.get('platform', ''),
            "count": d['count'],
        }, f"Generate {d['kind']}: {d['brief'][:80]}", risk_tier=1)

    # ---------- Campaign launch (multi-platform, always human) ----------
    @action(detail=False, methods=['post'], url_path='campaigns/launch')
    def launch_campaign(self, request):
        """Launch across platforms — one proposal per platform, always T3."""
        s = LaunchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        results = []
        per_platform = d['total_budget_paise'] // len(d['platforms'])
        for platform in d['platforms']:
            resp = _submit(request, f"{platform}.create_campaign", {
                "name": d['name'], "objective": d['objective'],
                "daily_budget": per_platform / 100, "spend_paise": per_platform,
            }, f"Launch {d['name']} on {platform}", risk_tier=3,
                evidence={"source": "api", "platform": platform})
            results.append(resp.data)
        return Response({"proposals": results}, status=status.HTTP_202_ACCEPTED)

    # ---------- Read-only aggregates ----------
    @action(detail=False, methods=['get'], url_path='pipeline')
    def pipeline(self, request):
        """Lead pipeline aggregates — stage counts, totals, consent coverage."""
        from django.db.models import Count
        from core.models import Lead
        leads = Lead.objects.filter(org=request.org)
        stages = dict(leads.values_list('stage').annotate(c=Count('id')))
        order = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost']
        return Response({
            "total": leads.count(),
            "stages": [{"stage": s_, "count": stages.get(s_, 0)} for s_ in order],
            "consented_whatsapp": leads.filter(has_whatsapp_consent=True).count(),
            "opted_out": leads.exclude(opted_out_at__isnull=True).count(),
        })
