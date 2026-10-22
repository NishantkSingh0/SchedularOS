"""
Analytics API
Org-scoped aggregate endpoints powering dashboard charts.

Data-integrity rule (per spec): only real, computed data is returned.
Metrics with no backing source return ``available: false`` rather than
fabricated values.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncDate
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


def _daterange(request, default_days=30):
    """Parse ?days= / ?from=&to= into (start, end) datetimes."""
    end = timezone.now()
    try:
        days = int(request.query_params.get('days', default_days))
    except (TypeError, ValueError):
        days = default_days
    days = max(1, min(days, 365))
    return end - timedelta(days=days), end


def _daily_counts(queryset, date_field, start, end):
    """Return [{date, count}] per day for queryset within range."""
    rows = (
        queryset.filter(**{f"{date_field}__range": (start, end)})
        .annotate(day=TruncDate(date_field))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    by_day = {r['day'].isoformat(): r['count'] for r in rows}
    out, cursor = [], start.date()
    while cursor <= end.date():
        out.append({"date": cursor.isoformat(), "count": by_day.get(cursor.isoformat(), 0)})
        cursor += timedelta(days=1)
    return out


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # ---------- KPIs ----------
    @action(detail=False, methods=['get'])
    def kpis(self, request):
        from core.models import Lead, Conversation, Message
        from orchestration.models import WorkflowRun, RunStep
        from proposals.models import Proposal

        org = request.org
        leads = Lead.objects.filter(org=org)
        runs = WorkflowRun.objects.filter(org=org)
        proposals = Proposal.objects.filter(org=org)

        executed = proposals.filter(status='executed')
        spend_paise = sum(
            (p.payload or {}).get('spend_paise', 0) or 0 for p in executed
        )

        total_leads = leads.count()
        won = leads.filter(stage='won').count()

        return Response({
            "total_leads": total_leads,
            "won_leads": won,
            "conversion_rate": round(won / total_leads * 100, 1) if total_leads else 0,
            "leads_by_stage": dict(leads.values_list('stage').annotate(c=Count('id'))),
            "total_spend_paise": spend_paise,
            "active_workflows": runs.filter(status='running').count(),
            "completed_workflows": runs.filter(status='completed').count(),
            "failed_workflows": runs.filter(status='failed').count(),
            "pending_proposals": proposals.filter(status='pending').count(),
            "executed_proposals": executed.count(),
            "rejected_proposals": proposals.filter(status='rejected').count(),
            "conversations": Conversation.objects.filter(org=org).count(),
            "messages_inbound": Message.objects.filter(conversation__org=org, direction='inbound').count(),
            "messages_outbound": Message.objects.filter(conversation__org=org, direction='outbound').count(),
            "data_quality": {
                "revenue": "unavailable — no revenue/order source connected",
                "roas": "unavailable — requires revenue attribution",
                "spend": "from executed proposals carrying spend_paise",
            },
        })

    # ---------- Leads ----------
    @action(detail=False, methods=['get'])
    def lead_trend(self, request):
        from core.models import Lead
        start, end = _daterange(request)
        return Response({"series": _daily_counts(Lead.objects.filter(org=request.org), 'created_at', start, end)})

    @action(detail=False, methods=['get'])
    def funnel(self, request):
        from core.models import Lead
        order = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost']
        counts = dict(
            Lead.objects.filter(org=request.org)
            .values_list('stage').annotate(c=Count('id'))
        )
        return Response({"stages": [{"stage": s, "count": counts.get(s, 0)} for s in order]})

    @action(detail=False, methods=['get'])
    def lead_sources(self, request):
        """Lead model has no source field — distribution by tags instead."""
        from core.models import Lead
        tag_counts = {}
        for tags in Lead.objects.filter(org=request.org).values_list('tags', flat=True):
            for t in (tags or ['untagged']) or ['untagged']:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        return Response({
            "sources": [{"name": k, "count": v} for k, v in sorted(tag_counts.items(), key=lambda x: -x[1])],
            "note": "Lead model has no dedicated source field — grouped by lead tags.",
        })

    @action(detail=False, methods=['get'])
    def lead_score_distribution(self, request):
        from core.models import Lead
        buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for score in Lead.objects.filter(org=request.org).values_list('score', flat=True):
            s = score or 0
            key = ("0-20" if s <= 20 else "21-40" if s <= 40 else
                   "41-60" if s <= 60 else "61-80" if s <= 80 else "81-100")
            buckets[key] += 1
        return Response({"buckets": [{"range": k, "count": v} for k, v in buckets.items()]})

    # ---------- Agentic execution ----------
    @action(detail=False, methods=['get'])
    def agent_productivity(self, request):
        from orchestration.models import RunStep, AgentRun
        org = request.org
        steps = (
            RunStep.objects.filter(run__org=org)
            .values('agent', 'state').annotate(c=Count('id'))
        )
        by_agent = {}
        for row in steps:
            a = by_agent.setdefault(row['agent'], {"scheduled": 0, "running": 0,
                "done": 0, "awaiting_human": 0, "failed": 0, "cancelled": 0})
            a[row['state']] = row['c']
        runs = (
            AgentRun.objects.filter(step__run__org=org)
            .values('agent').annotate(runs=Count('id'), proposals=Sum('proposal_count'))
        )
        for r in runs:
            by_agent.setdefault(r['agent'], {})['agent_runs'] = r['runs']
            by_agent[r['agent']]['proposals'] = r['proposals'] or 0
        return Response({"agents": [{"agent": k, **v} for k, v in sorted(by_agent.items())]})

    @action(detail=False, methods=['get'])
    def workflow_stats(self, request):
        from orchestration.models import WorkflowRun, RunStep
        org = request.org
        status_counts = dict(
            WorkflowRun.objects.filter(org=org).values_list('status').annotate(c=Count('id'))
        )
        completed = WorkflowRun.objects.filter(org=org, status='completed')
        durations = [(r.updated_at - r.created_at).total_seconds() for r in completed[:200]]
        step_states = dict(
            RunStep.objects.filter(run__org=org).values_list('state').annotate(c=Count('id'))
        )
        return Response({
            "by_status": [{"status": k, "count": v} for k, v in status_counts.items()],
            "step_states": step_states,
            "avg_completion_seconds": round(sum(durations) / len(durations), 1) if durations else None,
        })

    @action(detail=False, methods=['get'])
    def proposal_stats(self, request):
        from proposals.models import Proposal, Approval
        org = request.org
        by_status = dict(
            Proposal.objects.filter(org=org).values_list('status').annotate(c=Count('id'))
        )
        by_risk = dict(
            Proposal.objects.filter(org=org).values_list('risk_tier').annotate(c=Count('id'))
        )
        by_action = (
            Proposal.objects.filter(org=org)
            .values('action_type').annotate(c=Count('id')).order_by('-c')[:10]
        )
        decisions = Approval.objects.filter(proposal__org=org)
        decision_times = [
            (a.created_at - a.proposal.created_at).total_seconds()
            for a in decisions.select_related('proposal')[:200]
        ]
        return Response({
            "by_status": [{"status": k, "count": v} for k, v in by_status.items()],
            "by_risk_tier": [{"tier": k, "count": v} for k, v in sorted(by_risk.items())],
            "top_actions": list(by_action),
            "decisions": dict(decisions.values_list('decision').annotate(c=Count('id'))),
            "avg_decision_seconds": round(sum(decision_times) / len(decision_times), 1) if decision_times else None,
        })

    # ---------- Spend ----------
    @action(detail=False, methods=['get'])
    def spend_over_time(self, request):
        """Executed spend (paise) per day — only proposals that actually executed."""
        from proposals.models import Proposal
        start, end = _daterange(request)
        executed = Proposal.objects.filter(
            org=request.org, status='executed', executed_at__range=(start, end)
        )
        by_day = {}
        for p in executed:
            day = p.executed_at.date().isoformat()
            by_day[day] = by_day.get(day, 0) + ((p.payload or {}).get('spend_paise') or 0)
        out, cursor = [], start.date()
        while cursor <= end.date():
            out.append({"date": cursor.isoformat(), "spend_paise": by_day.get(cursor.isoformat(), 0)})
            cursor += timedelta(days=1)
        return Response({"series": out, "note": "Only executed proposals carrying spend_paise."})

    # ---------- Activity ----------
    @action(detail=False, methods=['get'])
    def activity(self, request):
        from core.models import AuditEvent
        limit = min(int(request.query_params.get('limit', 50)), 200)
        events = AuditEvent.objects.filter(org=request.org).order_by('-created_at')[:limit]
        return Response({"events": [{
            "id": str(e.id),
            "event_type": e.event_type,
            "proposal_id": str(e.proposal_id) if e.proposal_id else None,
            "metadata": e.metadata,
            "created_at": e.created_at.isoformat(),
        } for e in events]})

    # ---------- Conversations ----------
    @action(detail=False, methods=['get'])
    def message_trend(self, request):
        from core.models import Message
        start, end = _daterange(request)
        msgs = Message.objects.filter(conversation__org=request.org)
        return Response({
            "inbound": _daily_counts(msgs.filter(direction='inbound'), 'created_at', start, end),
            "outbound": _daily_counts(msgs.filter(direction='outbound'), 'created_at', start, end),
        })

    # ---------- Trust ----------
    @action(detail=False, methods=['get'])
    def trust(self, request):
        from core.models import AgentTrustState
        rows = AgentTrustState.objects.filter(org=request.org)
        return Response({"trust": [{
            "agent": t.agent, "action_type": t.action_type, "trust_level": t.trust_level,
            "approvals": t.approvals, "rejections": t.rejections,
            "total_decisions": t.total_decisions,
        } for t in rows]})

    # ---------- Ad campaigns ----------
    @action(detail=False, methods=['get'])
    def ad_campaigns(self, request):
        """Live ad campaigns from Meta when credentials are configured."""
        from django.conf import settings
        if not (settings.META_CONFIG.get('access_token') and settings.META_CONFIG.get('ad_account_id')):
            return Response({
                "campaigns": [],
                "available": False,
                "reason": "Meta Ads credentials not configured",
            })
        try:
            from connectors.meta_connector import get_meta_connector
            conn = get_meta_connector()
            campaigns = [
                {"id": c.id, "name": c.name, "status": c.status, "objective": c.objective,
                 "budget": c.budget, "spend": c.spend, "impressions": c.impressions,
                 "clicks": c.clicks, "conversions": c.conversions}
                for c in conn.get_campaigns()
            ]
            return Response({"campaigns": campaigns, "available": True})
        except Exception as e:
            return Response({"campaigns": [], "available": False, "reason": str(e)})

    # ---------- Integrations ----------
    @action(detail=False, methods=['get'])
    def integrations(self, request):
        """Connection status only — never exposes secret values."""
        from django.conf import settings
        def cfg_status(cfg, keys):
            return all(cfg.get(k) for k in keys)
        return Response({"integrations": [
            {"name": "Jev LLM", "category": "ai", "configured": bool(settings.LLM_CONFIG.get('jev_api_key'))},
            {"name": "OpenAI", "category": "ai", "configured": bool(settings.LLM_CONFIG.get('openai_api_key'))},
            {"name": "Meta (Ads + WhatsApp)", "category": "advertising",
             "configured": cfg_status(settings.META_CONFIG, ['access_token', 'ad_account_id'])},
            {"name": "Google Ads", "category": "advertising",
             "configured": cfg_status(settings.GOOGLE_ADS_CONFIG,
                ['developer_token', 'client_id', 'client_secret', 'refresh_token', 'customer_id'])},
            {"name": "Content Generation", "category": "creative",
             "configured": bool(settings.CONTENT_GEN_CONFIG.get('api_key'))},
            {"name": "Web Search (Bing)", "category": "research",
             "configured": bool(settings.SEARCH_CONFIG.get('api_key'))},
            {"name": "AWS SES Email", "category": "messaging",
             "configured": cfg_status(settings.EMAIL_CONFIG,
                ['aws_access_key_id', 'aws_secret_access_key', 'verified_sender'])},
            {"name": "WhatsApp Webhook", "category": "messaging",
             "configured": bool(__import__('os').getenv('WHATSAPP_VERIFY_TOKEN'))},
        ]})
