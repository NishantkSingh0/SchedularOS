from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from core.models import Organization, Brand, UserProfile, Lead
from core.serializers import OrganizationSerializer, BrandSerializer, UserProfileSerializer, LeadSerializer
from core.tasks import async_research_task, async_workflow_task, async_knowledge_store_task


class ResearchRequestSerializer(serializers.Serializer):
    """Serializer for research requests"""
    research_type = serializers.ChoiceField(choices=['market', 'competitors', 'audience'])
    industry = serializers.CharField(required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    product = serializers.CharField(required=False, allow_blank=True)
    company_context = serializers.CharField(required=False, allow_blank=True)
    async_mode = serializers.BooleanField(default=False)


class ResearchResponseSerializer(serializers.Serializer):
    """Serializer for research responses"""
    topic = serializers.CharField()
    findings = serializers.CharField()
    sources = serializers.ListField(child=serializers.CharField())
    confidence = serializers.FloatField()
    metadata = serializers.DictField()


class WorkflowRequestSerializer(serializers.Serializer):
    """Serializer for workflow requests"""
    workflow_type = serializers.ChoiceField(choices=['orchestrator', 'marketing'])
    goal = serializers.CharField()
    industry = serializers.CharField(required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    product = serializers.CharField(required=False, allow_blank=True)
    company_context = serializers.CharField(required=False, allow_blank=True)
    async_mode = serializers.BooleanField(default=False)


class WorkflowResponseSerializer(serializers.Serializer):
    """Serializer for workflow responses"""
    goal = serializers.CharField()
    current_step = serializers.CharField()
    research_results = serializers.ListField()
    proposals = serializers.ListField()
    errors = serializers.ListField()
    context = serializers.DictField()


class KnowledgeDocumentSerializer(serializers.Serializer):
    """Serializer for knowledge documents"""
    title = serializers.CharField()
    content = serializers.CharField()
    source = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)
    async_mode = serializers.BooleanField(default=False)


class SearchRequestSerializer(serializers.Serializer):
    """Serializer for knowledge search requests"""
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=5)


class ResearchViewSet(viewsets.ViewSet):
    """ViewSet for research operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def perform(self, request):
        """Perform research based on request parameters"""
        serializer = ResearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        research_type = data['research_type']
        
        # Async mode using Celery
        if data.get('async_mode', False):
            task = async_research_task.delay(
                research_type=research_type,
                params={
                    'industry': data.get('industry', ''),
                    'company_name': data.get('company_name', ''),
                    'product': data.get('product', ''),
                    'company_context': data.get('company_context', '')
                },
                org_id=str(request.org.id)
            )
            return Response({
                "task_id": task.id,
                "status": "processing",
                "message": "Research task started in background"
            })
        
        # Sync mode
        try:
            import sys
            import os
            packages_path = os.path.join(os.path.dirname(__file__), '../../../packages')
            agents_path = os.path.join(packages_path, 'agents')
            if packages_path not in sys.path:
                sys.path.insert(0, packages_path)
            if agents_path not in sys.path:
                sys.path.insert(0, agents_path)
            
            from research_agent import ResearchAgent
            
            research_agent = ResearchAgent()
            
            if research_type == 'market':
                result = research_agent.research_market(
                    industry=data.get('industry', ''),
                    company_context=data.get('company_context')
                )
            elif research_type == 'competitors':
                result = research_agent.research_competitors(
                    company_name=data.get('company_name', ''),
                    industry=data.get('industry', '')
                )
            elif research_type == 'audience':
                result = research_agent.research_audience(
                    product=data.get('product', ''),
                    industry=data.get('industry', '')
                )
            else:
                return Response(
                    {"error": f"Unknown research type: {research_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            response_serializer = ResearchResponseSerializer(result)
            return Response(response_serializer.data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WorkflowViewSet(viewsets.ViewSet):
    """ViewSet for workflow operations using LangGraph"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a workflow using LangGraph orchestration"""
        serializer = WorkflowRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Async mode using Celery
        if data.get('async_mode', False):
            task = async_workflow_task.delay(
                workflow_type=data['workflow_type'],
                goal=data['goal'],
                context={
                    "industry": data.get('industry', ''),
                    "company_name": data.get('company_name', ''),
                    "product": data.get('product', ''),
                    "company_context": data.get('company_context', '')
                },
                org_id=str(request.org.id)
            )
            return Response({
                "task_id": task.id,
                "status": "processing",
                "message": "Workflow task started in background"
            })
        
        # Sync mode
        try:
            import sys
            import os
            packages_path = os.path.join(os.path.dirname(__file__), '../../../packages')
            orchestration_path = os.path.join(packages_path, 'orchestration')
            if packages_path not in sys.path:
                sys.path.insert(0, packages_path)
            if orchestration_path not in sys.path:
                sys.path.insert(0, orchestration_path)
            
            from graph import OrchestratorGraph, MarketingWorkflowGraph
            
            context = {
                "industry": data.get('industry', ''),
                "company_name": data.get('company_name', ''),
                "product": data.get('product', ''),
                "company_context": data.get('company_context', '')
            }
            
            if data['workflow_type'] == 'orchestrator':
                graph = OrchestratorGraph()
                result = graph.run(data['goal'], context)
            elif data['workflow_type'] == 'marketing':
                graph = MarketingWorkflowGraph()
                result = graph.run(data['goal'], context)
            else:
                return Response(
                    {"error": f"Unknown workflow type: {data['workflow_type']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            response_data = {
                "goal": result["goal"],
                "current_step": result["current_step"],
                "research_results": result["research_results"],
                "proposals": result["proposals"],
                "errors": result["errors"],
                "context": result["context"]
            }
            
            return Response(response_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KnowledgeViewSet(viewsets.ViewSet):
    """ViewSet for knowledge base operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def store(self, request):
        """Store a document in the knowledge base"""
        serializer = KnowledgeDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Async mode using Celery
        if data.get('async_mode', False):
            task = async_knowledge_store_task.delay(
                document_data={
                    'title': data['title'],
                    'content': data['content'],
                    'source': data.get('source', 'manual'),
                    'metadata': data.get('metadata', {})
                },
                org_id=str(request.org.id)
            )
            return Response({
                "task_id": task.id,
                "status": "processing",
                "message": "Document storage task started in background"
            })
        
        # Sync mode
        try:
            import sys
            import os
            packages_path = os.path.join(os.path.dirname(__file__), '../../../packages')
            memory_path = os.path.join(packages_path, 'memory')
            if packages_path not in sys.path:
                sys.path.insert(0, packages_path)
            if memory_path not in sys.path:
                sys.path.insert(0, memory_path)
            
            from rag import get_rag_service
            
            rag_service = get_rag_service()
            doc_id = rag_service.store_document(
                org_id=str(request.org.id),
                title=data['title'],
                content=data['content'],
                source=data.get('source', 'manual'),
                metadata=data.get('metadata', {})
            )
            
            return Response({"id": doc_id, "message": "Document stored successfully"})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search the knowledge base"""
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            import sys
            import os
            packages_path = os.path.join(os.path.dirname(__file__), '../../../packages')
            memory_path = os.path.join(packages_path, 'memory')
            if packages_path not in sys.path:
                sys.path.insert(0, packages_path)
            if memory_path not in sys.path:
                sys.path.insert(0, memory_path)
            
            from rag import get_rag_service
            
            rag_service = get_rag_service()
            results = rag_service.search_documents(
                org_id=str(request.org.id),
                query=data['query'],
                top_k=data.get('top_k', 5)
            )
            
            return Response({"results": results})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Organization model"""
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        org = self.request.org
        if org:
            return Organization.objects.filter(id=org.id)
        return Organization.objects.none()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's organization"""
        if request.org:
            serializer = self.get_serializer(request.org)
            return Response(serializer.data)
        return Response({"error": "No organization found"}, status=status.HTTP_404_NOT_FOUND)


class BrandViewSet(viewsets.ModelViewSet):
    """ViewSet for Brand model"""
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        org = self.request.org
        if org:
            return Brand.objects.filter(org=org)
        return Brand.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(org=self.request.org)


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UserProfile model"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        profile = UserProfile.objects.get(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet for Lead model"""
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        org = self.request.org
        if org:
            queryset = Lead.objects.filter(org=org)
            stage = self.request.query_params.get('stage')
            if stage:
                queryset = queryset.filter(stage=stage)
            return queryset
        return Lead.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(org=self.request.org)
