from celery import shared_task
from proposals.models import Proposal
from connectors.executor import Executor
from django.utils import timezone


@shared_task(queue="executor", bind=True, max_retries=3)
def execute_proposal(self, proposal_id: str):
    """
    Execute an approved proposal.
    Only the Executor touches the outside world.
    """
    proposal = Proposal.objects.get(id=proposal_id)
    if proposal.status not in ("approved", "edited"):
        # Already executed/failed/rejected — nothing to do (idempotent)
        return {"proposal_id": proposal_id, "skipped": proposal.status}

    try:
        executor = Executor()
        result = executor.execute(proposal)
        
        proposal.mark_executed()

        # Record spend against the daily budget counter (enables policy cap checks)
        spend = proposal.payload.get("spend_paise") if proposal.payload else None
        if spend:
            try:
                import redis as redis_lib
                from django.conf import settings
                today = timezone.now().date().isoformat()
                redis_client = redis_lib.from_url(settings.REDIS_URL)
                spend_key = f"sos:{proposal.org_id}:budget:{proposal.step.agent}:{today}"
                redis_client.incrby(spend_key, int(spend))
                redis_client.expire(spend_key, 172800)  # keep for 2 days
            except Exception as e:
                print(f"Failed to record spend for proposal {proposal.id}: {e}")

        # Create audit event
        from core.models import AuditEvent
        AuditEvent.objects.create(
            org_id=proposal.org_id,
            event_type="proposal.executed",
            proposal_id=proposal.id,
            metadata={"result": result}
        )
        
        return {"proposal_id": proposal_id, "result": result}
    
    except Exception as e:
        proposal.mark_failed(str(e))
        if self.request.retries < 3:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        raise


@shared_task(queue="default")
def expire_stale_proposals():
    """
    Mark proposals as expired after 48 hours.
    Executed by Celery beat every 5 minutes.
    """
    from django.utils import timezone

    proposals = list(Proposal.objects.filter(
        status="pending",
        expires_at__lt=timezone.now()
    ).select_related('step'))

    step_ids = set()
    for p in proposals:
        p.status = "expired"
        p.save(update_fields=['status'])
        step_ids.add(str(p.step_id))

    # Resolve steps whose proposals all expired
    from orchestration.engine import resolve_step_after_decisions
    for step_id in step_ids:
        try:
            resolve_step_after_decisions(step_id)
        except Exception as e:
            print(f"Failed to resolve step {step_id} after expiry: {e}")

    return {"expired": len(proposals)}
