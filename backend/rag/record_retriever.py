"""
Entity-Isolated Record Retriever Module for RAG Subsystem

Provides similarity search across historical Store, Item, Customer, and Transaction records.
Guarantees entity isolation:
- Customer search -> customer_knowledge collection
- Store search    -> store_knowledge collection
- Item search     -> item_knowledge collection
"""
from __future__ import annotations
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple

from backend.rag.embedder import get_embedding, get_embeddings_batch
from backend.rag.vector_store import get_vector_collection, VectorDocument
from backend.rag.record_serializer import serialize_record_to_text


def extract_record_id(record: Dict[str, Any], entity_type: str = "general") -> str:
    """Extracts or generates a stable unique identifier for a record."""
    id_keys = [
        f"{entity_type}_id", f"{entity_type}_code", "id", "code",
        "customer_id", "store_id", "product_id", "item_id", "sku", "barcode", "roll_no", "reg_no"
    ]
    for k in id_keys:
        for rk, rv in record.items():
            if str(rk).lower().strip() == k and rv is not None and str(rv).strip():
                return str(rv).strip()
    return f"{entity_type}_{str(uuid.uuid4())[:8]}"


def ingest_record(
    record: Dict[str, Any],
    entity_type: str = "general",
    record_id: Optional[str] = None,
    original_record: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Ingests a single cleaned record into the corresponding entity vector collection."""
    if not record:
        return ""

    actual_id = record_id or extract_record_id(record, entity_type)
    text = serialize_record_to_text(record, entity_type)
    vector = get_embedding(text)

    coll = get_vector_collection(entity_type)
    doc = VectorDocument(
        doc_id=actual_id,
        vector=vector,
        text=text,
        entity_type=entity_type,
        cleaned_record=record,
        original_record=original_record or record,
        metadata=metadata or {},
        timestamp=time.time()
    )
    coll.upsert(doc)
    return actual_id


def ingest_records_batch(
    records: List[Dict[str, Any]],
    entity_type: str = "general",
    original_records: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Ingests a batch of records efficiently into the entity vector collection."""
    if not records:
        return 0

    coll = get_vector_collection(entity_type)
    docs_to_add: List[VectorDocument] = []
    
    texts = [serialize_record_to_text(r, entity_type) for r in records]
    vectors = get_embeddings_batch(texts)

    for idx, (rec, text, vec) in enumerate(zip(records, texts, vectors)):
        orig = original_records[idx] if original_records and idx < len(original_records) else rec
        rec_id = extract_record_id(rec, entity_type)
        docs_to_add.append(VectorDocument(
            doc_id=rec_id,
            vector=vec,
            text=text,
            entity_type=entity_type,
            cleaned_record=rec,
            original_record=orig,
            metadata=metadata or {},
            timestamp=time.time()
        ))

    coll.upsert_batch(docs_to_add)
    return len(docs_to_add)


def search_similar_records(
    query_record: Dict[str, Any],
    entity_type: str = "general",
    top_k: int = 5,
    min_score: float = 0.35,
    exclude_record_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves the Top-K most similar historical records for a given input record.
    Keeps retrieval isolated to the specific entity knowledge base.
    
    Returns a list of structured candidate objects:
    [
      {
        "record_id": "CUS001",
        "similarity_score": 0.94,
        "text": "...",
        "cleaned_record": {...},
        "original_record": {...}
      }
    ]
    """
    if not query_record:
        return []

    coll = get_vector_collection(entity_type)
    if coll.count() == 0:
        return []

    query_text = serialize_record_to_text(query_record, entity_type)
    query_vector = get_embedding(query_text)

    filter_fn = None
    if exclude_record_id:
        filter_fn = lambda d: d.doc_id != exclude_record_id

    matches = coll.search(query_vector, top_k=top_k, min_score=min_score, filter_fn=filter_fn)

    results = []
    for doc, score in matches:
        results.append({
            "record_id": doc.doc_id,
            "similarity_score": round(score, 3),
            "text": doc.text,
            "cleaned_record": doc.cleaned_record,
            "original_record": doc.original_record,
            "entity_type": doc.entity_type
        })

    return results
