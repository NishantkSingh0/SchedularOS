"""
RAG (Retrieval-Augmented Generation) Module
Implements semantic search using pgvector and document chunking
"""
import os
import sys
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import re

# Add parent packages to path
current_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.dirname(current_dir)
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)

from llm_gateway.gateway import LLMGateway, LLMMessage, get_llm_gateway


@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class RetrievedDocument:
    """Represents a retrieved document with similarity score"""
    id: str
    title: str
    content: str
    similarity: float
    metadata: Dict[str, Any]


class RAGService:
    """Service for RAG operations using pgvector"""
    
    def __init__(self):
        """Initialize RAG service"""
        self.llm_gateway = get_llm_gateway()
        self.chunk_size = 500  # Characters per chunk
        self.chunk_overlap = 50  # Characters overlap between chunks
    
    def chunk_document(self, content: str, document_id: str) -> List[DocumentChunk]:
        """
        Split a document into chunks
        
        Args:
            content: Document content
            document_id: Document ID
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                chunks.append(DocumentChunk(
                    id=f"{document_id}-{chunk_index}",
                    document_id=document_id,
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    metadata={"chunk_type": "paragraph"}
                ))
                chunk_index += 1
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add remaining content
        if current_chunk:
            chunks.append(DocumentChunk(
                id=f"{document_id}-{chunk_index}",
                document_id=document_id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                metadata={"chunk_type": "paragraph"}
            ))
        
        return chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using LLM provider
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding
        """
        # Use real embeddings when a provider is configured; otherwise fall
        # back to a deterministic mock embedding (dev/offline mode)
        try:
            from llm_gateway.client import embed_text
            return embed_text(text)
        except Exception:
            import hashlib
            import numpy as np

            # Create a deterministic mock embedding based on text hash
            hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
            np.random.seed(hash_value % (2**32 - 1))  # Ensure seed is within valid range
            return np.random.randn(1536).tolist()
    
    def store_document(self, org_id: str, title: str, content: str, source: str = "manual", metadata: Optional[Dict] = None) -> str:
        """
        Store a document in the knowledge base
        
        Args:
            org_id: Organization ID
            title: Document title
            content: Document content
            source: Source of the document
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        from core.models import KnowledgeDocument, Organization
        
        # Get organization
        org = Organization.objects.get(id=org_id)
        
        # Create document with a real embedding of its content
        document = KnowledgeDocument.objects.create(
            org=org,
            title=title,
            content=content,
            embedding=self.generate_embedding(content[:2000]),
            metadata=metadata or {},
            source=source,
            chunk_index=0
        )
        
        # Chunk the document
        chunks = self.chunk_document(content, str(document.id))
        
        # Store each chunk as a separate document
        for chunk in chunks:
            embedding = self.generate_embedding(chunk.content)
            
            KnowledgeDocument.objects.create(
                org=org,
                title=f"{title} (chunk {chunk.chunk_index})",
                content=chunk.content,
                embedding=embedding,
                metadata={**(metadata or {}), "parent_document_id": str(document.id), "chunk_index": chunk.chunk_index},
                source=source,
                chunk_index=chunk.chunk_index
            )
        
        return str(document.id)
    
    def retrieve_relevant_docs(self, org_id: str, query: str, top_k: int = 5) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents using semantic search
        
        Args:
            org_id: Organization ID
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievedDocument objects
        """
        from core.models import KnowledgeDocument
        from django.db.models import Q
        
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)
        
        # Get all documents for the organization
        documents = KnowledgeDocument.objects.filter(org_id=org_id).exclude(embedding__isnull=True)
        
        # Calculate cosine similarity manually (in production, use pgvector's similarity search)
        results = []
        for doc in documents:
            if doc.embedding and len(doc.embedding) == 1536:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                results.append(RetrievedDocument(
                    id=str(doc.id),
                    title=doc.title,
                    content=doc.content,
                    similarity=similarity,
                    metadata=doc.metadata
                ))
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        a = np.array(vec1)
        b = np.array(vec2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def build_knowledge_context(self, org_id: str, query: str, max_tokens: int = 2000) -> str:
        """
        Build knowledge context from retrieved documents
        
        Args:
            org_id: Organization ID
            query: Search query
            max_tokens: Maximum tokens in context
            
        Returns:
            Formatted knowledge context string
        """
        retrieved_docs = self.retrieve_relevant_docs(org_id, query, top_k=5)
        
        if not retrieved_docs:
            return "No relevant documents found."
        
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Approximate 4 chars per token
        
        for doc in retrieved_docs:
            if total_chars + len(doc.content) > max_chars:
                break
            
            context_parts.append(f"[{doc.title}]\n{doc.content}\n")
            total_chars += len(doc.content)
        
        return "\n".join(context_parts)
    
    def search_documents(self, org_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword search
        
        Args:
            org_id: Organization ID
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of document dictionaries
        """
        from core.models import KnowledgeDocument
        from django.db.models import Q
        
        # Semantic search
        semantic_results = self.retrieve_relevant_docs(org_id, query, top_k)
        
        # Keyword search
        keyword_results = KnowledgeDocument.objects.filter(
            org_id=org_id,
            content__icontains=query
        )[:top_k]
        
        # Combine and deduplicate
        seen_ids = set()
        combined_results = []
        
        # Add semantic results first
        for doc in semantic_results:
            if doc.id not in seen_ids:
                combined_results.append({
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content,
                    "similarity": doc.similarity,
                    "metadata": doc.metadata,
                    "search_type": "semantic"
                })
                seen_ids.add(doc.id)
        
        # Add keyword results
        for doc in keyword_results:
            if str(doc.id) not in seen_ids:
                combined_results.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "content": doc.content,
                    "similarity": 0.0,
                    "metadata": doc.metadata,
                    "search_type": "keyword"
                })
                seen_ids.add(str(doc.id))
        
        return combined_results[:top_k]


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
