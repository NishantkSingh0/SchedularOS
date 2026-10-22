from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class AgentViewSet(viewsets.ViewSet):
    """Read-only viewset exposing the agent registry"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List all registered agents"""
        from agents.registry import list_agents, get_agent

        agents = []
        for name in list_agents():
            agent = get_agent(name)
            agents.append({
                "name": name,
                "model_tier": agent.model_tier.value,
                "queue": agent.queue,
                "default_risk_tier": agent.default_risk_tier,
            })
        return Response({"agents": agents})

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a single agent ad-hoc against a lead/goal"""
        goal = request.data.get('goal')
        agent_name = request.data.get('agent')
        if not goal or not agent_name:
            return Response(
                {"error": "agent and goal are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from core.models import Lead, Brand
        from orchestration.engine import create_workflow

        lead = Lead.objects.filter(id=request.data.get('lead_id'), org=request.org).first() \
            if request.data.get('lead_id') else None
        brand = Brand.objects.filter(id=request.data.get('brand_id'), org=request.org).first() \
            if request.data.get('brand_id') else None

        run = create_workflow(
            org=request.org,
            goal=goal,
            steps=[{"agent": agent_name, "delay_minutes": 0}],
            lead=lead,
            brand=brand,
        )
        return Response({"workflow_id": str(run.id)}, status=status.HTTP_202_ACCEPTED)
