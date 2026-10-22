from celery import shared_task
from django.db import transaction
from django.utils import timezone
from orchestration.models import RunStep, AgentRun
from orchestration.context import build_run_context
from orchestration.locks import lead_lock_context
from orchestration.engine import advance_run
from agents.registry import get_agent
from core.policy import submit_proposal
from django.conf import settings
import redis


@shared_task(queue="default", bind=True, max_retries=3)
def run_step(self, step_id: str):
    """
    Execute a single workflow step.
    """
    redis_client = redis.from_url(settings.REDIS_URL)
    
    with transaction.atomic():
        # Fetch step with lock
        step = RunStep.objects.select_for_update().get(id=step_id)
        
        # Terminal states are never re-executed (idempotent redelivery)
        if step.state in ('done', 'cancelled', 'awaiting_human'):
            return

        # Check idempotency
        idempotency_key = f"run:{step.idempotency_key}:attempt:{self.request.retries}"
        if redis_client.set(f"sos:{step.run.org.id}:idem:{idempotency_key}", "1", nx=True, ex=300):
            pass  # First attempt
        else:
            print(f"Step {step_id} already attempted, skipping")
            return

        # Mark as running
        step.mark_running()
    
    try:
        # Acquire lead lock if lead exists
        if step.run.lead:
            with lead_lock_context(str(step.run.org.id), str(step.run.lead.id), redis_client):
                return _execute_step_logic(step, redis_client)
        else:
            return _execute_step_logic(step, redis_client)
    
    except Exception as e:
        step.mark_failed(str(e))
        if self.request.retries < 3:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        step.run.mark_failed()
        raise


def _execute_step_logic(step, redis_client):
    """Execute the actual step logic"""
    # Build context
    ctx = build_run_context(step)
    
    # Get agent
    agent = get_agent(step.agent)
    
    # Run agent
    proposals = agent.run(ctx)
    
    # Record agent run
    AgentRun.objects.create(
        step=step,
        agent=step.agent,
        input_context=ctx.to_dict(),
        output={"proposals": proposals},
        proposal_count=len(proposals)
    )
    
    # Submit proposals
    needs_human = False
    for proposal_data in proposals:
        result = submit_proposal(
            org_id=str(step.run.org.id),
            step=step,
            proposal_data=proposal_data,
            redis_client=redis_client
        )
        if result.get("blocked"):
            from core.models import AuditEvent
            AuditEvent.objects.create(
                org_id=step.run.org_id,
                event_type="proposal.blocked",
                metadata={"agent": step.agent,
                          "action_type": proposal_data.get("action_type"),
                          "reason": result.get("reason")}
            )
        if result.get("needs_human"):
            needs_human = True
    
    # Mark step status
    if needs_human:
        step.mark_awaiting_human()
    else:
        step.mark_done()
        # Advance to next step
        advance_run(str(step.id))
    
    return {"step_id": str(step.id), "proposals": len(proposals), "needs_human": needs_human}


@shared_task(queue="default")
def scan_due_steps():
    """
    Scan for due steps every 30 seconds.
    Executed by Celery beat.
    """
    from orchestration.tasks import run_step
    from orchestration.engine import _agent_to_queue
    
    redis_client = redis.from_url(settings.REDIS_URL)
    
    with transaction.atomic():
        due_steps = (
            RunStep.objects
            .select_for_update(skip_locked=True)
            .filter(state="scheduled", run_at__lte=timezone.now())[:50]
        )
        
        for step in due_steps:
            # Check idempotency
            idempotency_key = f"dispatch:{step.id}"
            if redis_client.set(f"sos:{step.run.org.id}:idem:{idempotency_key}", "1", nx=True, ex=300):
                step.state = "running"
                step.save()
                run_step.apply_async(args=(str(step.id),), queue=_agent_to_queue(step.agent))
    
    return {"scanned": len(due_steps)}


@shared_task(queue="default")
def create_workflow_from_goal(org_id: str, goal: str):
    """
    Create a workflow from a natural language goal.
    Called by the API when user launches a goal.
    """
    from core.models import Organization
    from orchestration.engine import create_workflow
    from agents.orchestrator import OrchestratorAgent
    
    # Get organization
    org = Organization.objects.get(id=org_id)

    # Use orchestrator to decompose goal
    orchestrator = OrchestratorAgent()
    try:
        result = orchestrator.plan(goal, org_id)
    except Exception as e:
        from core.models import AuditEvent
        AuditEvent.objects.create(
            org_id=org_id,
            event_type="workflow.plan_failed",
            metadata={"goal": goal, "error": str(e)}
        )
        raise

    # Create workflow
    steps = result.get("steps", [])
    run = create_workflow(org, goal, steps)

    if not steps:
        run.mark_failed()
        from core.models import AuditEvent
        AuditEvent.objects.create(
            org_id=org_id,
            event_type="workflow.plan_failed",
            metadata={"goal": goal, "error": "Orchestrator returned no steps", "plan": result}
        )

    return {"workflow_id": str(run.id), "steps": len(steps)}
