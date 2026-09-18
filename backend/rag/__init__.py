"""
RAG (Retrieval-Augmented Generation) Subsystem for Data-Clean

Provides:
1. Entity-isolated Record Retrieval & Vector Search (Store, Item, Customer, Transaction)
2. Schema Knowledge Base & Unfamiliar Column Mapping RAG
3. Groq LLM Semantic Candidate Explanation Layer
4. Integration bridges for deterministic Record Matching
"""
from backend.rag.embedder import get_embedding, get_embeddings_batch, cosine_similarity
from backend.rag.vector_store import (
    VectorDocument,
    VectorCollection,
    VectorStoreManager,
    get_vector_collection
)
from backend.rag.record_serializer import serialize_record_to_text, serialize_schema_alias
from backend.rag.record_retriever import (
    ingest_record,
    ingest_records_batch,
    search_similar_records
)
from backend.rag.schema_retriever import (
    retrieve_schema_mapping_for_column,
    retrieve_batch_schema_mappings,
    seed_schema_knowledge
)
from backend.rag.llm_rag_analyzer import analyze_candidate_with_llm, heuristic_rag_analysis

__all__ = [
    "get_embedding",
    "get_embeddings_batch",
    "cosine_similarity",
    "VectorDocument",
    "VectorCollection",
    "VectorStoreManager",
    "get_vector_collection",
    "serialize_record_to_text",
    "serialize_schema_alias",
    "ingest_record",
    "ingest_records_batch",
    "search_similar_records",
    "retrieve_schema_mapping_for_column",
    "retrieve_batch_schema_mappings",
    "seed_schema_knowledge",
    "analyze_candidate_with_llm",
    "heuristic_rag_analysis"
]
