from celery import shared_task
from django.utils import timezone
import redis
from django.conf import settings
import sys
import os

# Add packages to path
packages_path = os.path.join(os.path.dirname(__file__), '../../packages')
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)


@shared_task(queue="default")
def reset_daily_budgets():
    """
    Reset daily budget counters at midnight UTC.
    Executed by Celery beat.
    """
    redis_client = redis.from_url(settings.REDIS_URL)
    
    # Get all budget keys (pattern: sos:{org}:budget:{agent}:{date})
    # In production, you'd scan for keys and delete previous day's counters
    # For now, this is a placeholder
    
    return {"reset": True}


@shared_task(queue="realtime")
def async_research_task(research_type: str, params: dict, org_id: str):
    """
    Asynchronous research task
    """
    from agents.research_agent import ResearchAgent
    
    research_agent = ResearchAgent()
    
    if research_type == 'market':
        result = research_agent.research_market(
            industry=params.get('industry', ''),
            company_context=params.get('company_context')
        )
    elif research_type == 'competitors':
        result = research_agent.research_competitors(
            company_name=params.get('company_name', ''),
            industry=params.get('industry', '')
        )
    elif research_type == 'audience':
        result = research_agent.research_audience(
            product=params.get('product', ''),
            industry=params.get('industry', '')
        )
    else:
        return {"error": f"Unknown research type: {research_type}"}
    
    return {
        "research_type": research_type,
        "result": result.__dict__,
        "org_id": org_id
    }


@shared_task(queue="realtime")
def async_workflow_task(workflow_type: str, goal: str, context: dict, org_id: str):
    """
    Asynchronous workflow execution task
    """
    # packages/orchestration is shadowed by the Django 'orchestration' app,
    # so add the package dir to sys.path and import the module directly
    graph_path = os.path.join(packages_path, 'orchestration')
    if graph_path not in sys.path:
        sys.path.insert(0, graph_path)
    from graph import OrchestratorGraph, MarketingWorkflowGraph
    
    if workflow_type == 'orchestrator':
        graph = OrchestratorGraph()
    elif workflow_type == 'marketing':
        graph = MarketingWorkflowGraph()
    else:
        return {"error": f"Unknown workflow type: {workflow_type}"}
    
    result = graph.run(goal, context)
    
    return {
        "workflow_type": workflow_type,
        "result": result,
        "org_id": org_id
    }


@shared_task(queue="bulk")
def async_knowledge_store_task(document_data: dict, org_id: str):
    """
    Asynchronous knowledge document storage task
    """
    from memory.rag import get_rag_service
    
    rag_service = get_rag_service()
    doc_id = rag_service.store_document(
        org_id=org_id,
        title=document_data['title'],
        content=document_data['content'],
        source=document_data.get('source', 'manual'),
        metadata=document_data.get('metadata', {})
    )
    
    return {
        "document_id": doc_id,
        "org_id": org_id
    }
