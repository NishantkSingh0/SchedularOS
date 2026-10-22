from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from core.models import Lead, Brand
from orchestration.models import WorkflowRun, RunStep


def create_workflow(org, goal: str, steps: list, lead: Lead = None, brand: Brand = None):
    """
    Create a new workflow with steps.
    All database operations happen in a single transaction.
    """
    from orchestration.tasks import run_step
    
    with transaction.atomic():
        # Create workflow run
        run = WorkflowRun.objects.create(
            org=org,
            goal=goal,
            lead=lead,
            brand=brand,
            status='planning'
        )
        
        # Create steps
        for i, step_def in enumerate(steps):
            delay_minutes = step_def.get("delay_minutes", 0)
            run_at = timezone.now() + timedelta(minutes=delay_minutes)
            
            RunStep.objects.create(
                run=run,
                agent=step_def["agent"],
                state="scheduled",
                run_at=run_at,
                idempotency_key=f"step:{run.id}:{i}:{step_def['agent']}"
            )
        
        # Mark as running
        run.mark_running()
        
        # Dispatch first step if it's immediate
        first_step = run.steps.filter(run_at__lte=timezone.now()).first()
        if first_step:
            run_step.apply_async(args=(str(first_step.id),), queue=_agent_to_queue(first_step.agent))
        
        return run


def _agent_to_queue(agent_name: str) -> str:
    """Map agent name to Celery queue"""
    from agents.registry import get_agent
    
    agent = get_agent(agent_name)
    return agent.queue


def advance_run(step_id: str):
    """
    Advance a workflow to the next step after current step completes.
    """
    from orchestration.models import RunStep, WorkflowRun
    from orchestration.tasks import run_step
    
    step = RunStep.objects.get(id=step_id)
    run = step.run
    
    # Check if there are more steps
    next_step = run.steps.filter(
        state='scheduled',
        run_at__lte=timezone.now()
    ).order_by('run_at').first()
    
    if next_step:
        # Dispatch next step
        run_step.apply_async(args=(str(next_step.id),), queue=_agent_to_queue(next_step.agent))
    else:
        # Check if all steps are done
        pending_steps = run.steps.filter(state__in=['scheduled', 'running', 'awaiting_human'])
        if not pending_steps:
            run.mark_completed()


def resolve_step_after_decisions(step_id: str):
    """
    Called after a human decision on a proposal. If no proposals on the step
    remain pending, resolve the step:
      - any proposal approved/edited -> step done, advance run
      - all proposals rejected/expired -> step failed, run failed (no further processing)
    """
    step = RunStep.objects.get(id=step_id)
    run = step.run

    pending = step.proposals.filter(status='pending')
    if pending.exists():
        return  # still waiting on humans

    approved = step.proposals.filter(status__in=['approved', 'edited', 'executed'])
    if approved.exists():
        step.mark_done()
        advance_run(str(step.id))
    else:
        step.mark_failed("all proposals rejected or expired")
        run.mark_failed()


def cancel_workflow(run_id: str):
    """
    Cancel a workflow and all pending steps.
    """
    from orchestration.models import WorkflowRun, RunStep
    
    with transaction.atomic():
        run = WorkflowRun.objects.get(id=run_id)
        run.mark_cancelled()
        
        # Cancel all pending steps
        run.steps.filter(state__in=['scheduled', 'awaiting_human']).update(
            state='cancelled',
            completed_at=timezone.now()
        )


def pause_workflow(run_id: str):
    """
    Pause a workflow.
    """
    from orchestration.models import WorkflowRun
    
    run = WorkflowRun.objects.get(id=run_id)
    run.mark_paused()


def resume_workflow(run_id: str):
    """
    Resume a paused workflow.
    """
    from orchestration.models import WorkflowRun, RunStep
    from orchestration.tasks import run_step
    
    with transaction.atomic():
        run = WorkflowRun.objects.get(id=run_id)
        run.status = 'running'
        run.save()
        
        # Dispatch due steps
        due_steps = run.steps.filter(
            state='scheduled',
            run_at__lte=timezone.now()
        )
        
        for step in due_steps:
            run_step.apply_async(args=(str(step.id),), queue=_agent_to_queue(step.agent))
