from typing import List, Dict
from core.models import KnowledgeDocument


def retrieve_relevant_docs(org_id: str, query: str, limit: int = 3) -> List[Dict]:
    """
    Retrieve relevant documents from the knowledge base using semantic search.
    Uses pgvector cosine distance when embeddings are available; falls back to
    keyword (Jaccard) matching when no embedding provider is configured.
    """
    # Try real semantic search first
    try:
        return _retrieve_semantic(org_id, query, limit)
    except Exception:
        pass

    # Fallback: keyword-based retrieval
    query_words = set(query.lower().split())
    
    docs = KnowledgeDocument.objects.filter(org_id=org_id)
    
    scored_docs = []
    for doc in docs:
        doc_words = set(doc.content.lower().split())
        # Calculate Jaccard similarity
        intersection = len(query_words & doc_words)
        union = len(query_words | doc_words)
        similarity = intersection / union if union > 0 else 0
        
        if similarity > 0:
            scored_docs.append({
                "id": str(doc.id),
                "title": doc.title,
                "content": doc.content,
                "metadata": doc.metadata,
                "similarity": similarity
            })
    
    # Sort by similarity and return top N
    scored_docs.sort(key=lambda x: x["similarity"], reverse=True)
    return scored_docs[:limit]


def _retrieve_semantic(org_id: str, query: str, limit: int) -> List[Dict]:
    """Semantic retrieval via pgvector cosine distance."""
    from llm_gateway.client import embed_text
    from pgvector.django import CosineDistance

    query_embedding = embed_text(query)

    docs = (
        KnowledgeDocument.objects
        .filter(org_id=org_id)
        .exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance('embedding', query_embedding))
        .order_by('distance')[:limit]
    )

    return [
        {
            "id": str(doc.id),
            "title": doc.title,
            "content": doc.content,
            "metadata": doc.metadata,
            "similarity": max(0.0, 1.0 - float(doc.distance)),
        }
        for doc in docs
    ]


def build_knowledge_context(docs: List[Dict]) -> str:
    """
    Build a formatted context string from retrieved documents.
    """
    if not docs:
        return "No relevant knowledge found."
    
    context_parts = []
    for doc in docs:
        context_parts.append(f"""
[Knowledge Snippet ID: {doc['id']}]
Title: {doc['title']}
Content: {doc['content']}
Similarity: {doc['similarity']:.2f}
""")
    
    return "\n".join(context_parts)
