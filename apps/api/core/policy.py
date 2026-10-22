from typing import Dict, Any
from enum import Enum
from django.utils import timezone
from django.db import transaction
import redis
import uuid


class RiskTier(Enum):
    """Risk tiers for proposals"""
    T0 = 0  # Internal only, always auto-approved
    T1 = 1  # Low risk, auto at L2+
    T2 = 2  # Medium risk, human approval required
    T3 = 3  # High risk, always human approval


class TrustLevel(Enum):
    """Trust levels for agents"""
    L0 = 0  # Shadow mode - proposals written but not executed
    L1 = 1  # Default - approve all
    L2 = 2  # Earned - auto-approve T0/T1
    L3 = 3  # High trust - auto-approve T0/T1/T2


def submit_proposal(org_id: str, step, proposal_data: Dict[str, Any], redis_client=None) -> Dict[str, Any]:
    """
    The policy engine - gatekeeper between agent proposals and execution.
    8-step validation flow.
    """
    from core.models import AuditEvent, AgentTrustState, Budget
    from proposals.models import Proposal
    from proposals.tasks import execute_proposal
    from django.conf import settings
    
    # Step 1: Schema check
    if "action_type" not in proposal_data:
        return {"blocked": True, "reason": "missing action_type"}
    if "rationale" not in proposal_data:
        return {"blocked": True, "reason": "missing rationale"}
    
    # Step 2: Grounding check
    risk_tier = proposal_data.get("risk_tier", 2)
    if risk_tier >= 2 and not proposal_data.get("evidence"):
        # Force to T2, require human review
        risk_tier = 2
        proposal_data["risk_tier"] = 2
    
    # Step 3: Consent check
    action_type = proposal_data["action_type"]
    if action_type.startswith("whatsapp"):
        from core.models import Lead
        lead = step.run.lead
        if lead and not lead.has_whatsapp_consent:
            return {"blocked": True, "reason": "no whatsapp consent"}
        if lead and lead.opted_out_at:
            return {"blocked": True, "reason": "lead opted out"}
    
    # Step 4: Budget check
    if "spend_paise" in proposal_data.get("payload", {}):
        spend = proposal_data["payload"]["spend_paise"]
        
        # Get daily spend from Redis
        if redis_client:
            today = timezone.now().date().isoformat()
            daily_spend_key = f"sos:{org_id}:budget:{step.agent}:{today}"
            daily_spend = int(redis_client.get(daily_spend_key) or 0)
        else:
            daily_spend = 0
        
        # Get budget caps
        try:
            budget = Budget.objects.get(org_id=org_id, agent=step.agent, period='daily')
        except Budget.DoesNotExist:
            budget = None
        
        if budget:
            if daily_spend + spend > budget.hard_cap:
                # Elevate to T3
                risk_tier = 3
                proposal_data["action_type"] = "budget.above_cap"
            elif daily_spend + spend > budget.soft_cap:
                # Log warning but allow
                print(f"Warning: Approaching budget cap for {step.agent}")
    
    # Step 5: Trust level lookup
    try:
        trust_state = AgentTrustState.objects.get(
            org_id=org_id,
            agent=step.agent,
            action_type=action_type
        )
        trust_level = TrustLevel(trust_state.trust_level)
    except AgentTrustState.DoesNotExist:
        trust_level = TrustLevel.L1
    
    # Step 6: Auto-approve decision
    should_auto = _should_auto_approve(risk_tier, trust_level, action_type)
    
    # Step 7: Write Proposal to Postgres
    with transaction.atomic():
        proposal = Proposal.objects.create(
            org_id=org_id,
            step=step,
            action_type=proposal_data["action_type"],
            payload=proposal_data.get("payload", {}),
            rationale=proposal_data["rationale"],
            evidence=proposal_data.get("evidence", {}),
            risk_tier=risk_tier,
            status="pending" if not should_auto else "approved",
            idempotency_key=f"{step.agent}:{action_type}:{step.id}:{uuid.uuid4()}",
            expires_at=timezone.now() + timezone.timedelta(hours=48) if not should_auto else None
        )
        
        AuditEvent.objects.create(
            org_id=org_id,
            event_type="proposal.created",
            proposal_id=proposal.id,
            metadata={"agent": step.agent, "action_type": action_type}
        )
    
    # Step 8a: Auto path
    if should_auto:
        proposal.status = "approved"
        proposal.save()
        execute_proposal.apply_async(queue="executor", args=(str(proposal.id),))
        return {"needs_human": False, "proposal_id": str(proposal.id)}
    
    # Step 8b: Human path
    # In production, this would broadcast via SSE
    print(f"New proposal awaiting human approval: {proposal.id}")
    
    return {"needs_human": True, "proposal_id": str(proposal.id)}


def _should_auto_approve(risk_tier: int, trust_level: TrustLevel, action_type: str) -> bool:
    """
    Determine if a proposal should be auto-approved based on risk tier (int 0-3)
    and trust level. Deny-by-default: only explicitly allowed combinations auto-approve.
    """
    # Specific actions that always require human approval
    ALWAYS_HUMAN = ["pricing", "legal", "bulk", "budget.above_cap"]
    if any(keyword in action_type for keyword in ALWAYS_HUMAN):
        return False

    # T3 actions always require human approval
    if risk_tier >= RiskTier.T3.value:
        return False

    # T0 always auto
    if risk_tier <= RiskTier.T0.value:
        return True

    # T1 auto at L2+
    if risk_tier <= RiskTier.T1.value:
        return trust_level.value >= TrustLevel.L2.value

    # T2 auto at L3 (earned autonomy)
    if risk_tier <= RiskTier.T2.value:
        return trust_level.value >= TrustLevel.L3.value

    return False


def update_trust_after_decision(org_id: str, agent: str, action_type: str, decision: str):
    """
    Update trust level based on human decisions.
    """
    from core.models import AgentTrustState
    
    trust_state, created = AgentTrustState.objects.get_or_create(
        org_id=org_id,
        agent=agent,
        action_type=action_type,
        defaults={"trust_level": 1}
    )
    
    trust_state.total_decisions += 1

    if decision in ("approved", "edited"):
        # 'edited' counts as approval: the human shaped it and let it run
        trust_state.approvals += 1
    else:
        trust_state.rejections += 1
        trust_state.last_rejection_at = timezone.now()
    
    # Calculate approval rate
    approval_rate = trust_state.approvals / trust_state.total_decisions
    
    # Promotion (L+1) requires all three:
    # - total decisions >= 200
    # - approval rate >= 95%
    # - no incident in last 30 days
    if (trust_state.total_decisions >= 200 and 
        approval_rate >= 0.95 and 
        (not trust_state.last_rejection_at or 
         (timezone.now() - trust_state.last_rejection_at).days > 30)):
        trust_state.trust_level = min(3, trust_state.trust_level + 1)
    
    # Demotion (L-1) triggers when:
    # - total decisions >= 20
    # - approval rate < 80% (immediate, no waiting period)
    if (trust_state.total_decisions >= 20 and approval_rate < 0.80):
        trust_state.trust_level = max(0, trust_state.trust_level - 1)
    
    trust_state.save()
