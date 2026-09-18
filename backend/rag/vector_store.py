"""
Vector Database & Collection Manager for RAG Subsystem

Provides fast in-memory similarity indexing with local disk persistence.
Maintains isolated collections for Store, Item, Customer, and Schema Knowledge.
"""
from __future__ import annotations
import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.rag.embedder import get_embedding, get_embeddings_batch, cosine_similarity

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_store", "vector_db")


class VectorDocument:
    """Represents an embedded document in a vector collection."""
    def __init__(
        self,
        doc_id: str,
        vector: List[float],
        text: str,
        entity_type: str,
        cleaned_record: Optional[Dict[str, Any]] = None,
        original_record: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ):
        self.doc_id = doc_id
        self.vector = vector
        self.text = text
        self.entity_type = entity_type
        self.cleaned_record = cleaned_record or {}
        self.original_record = original_record or {}
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "vector": self.vector,
            "text": self.text,
            "entity_type": self.entity_type,
            "cleaned_record": self.cleaned_record,
            "original_record": self.original_record,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VectorDocument:
        return cls(
            doc_id=data.get("doc_id", ""),
            vector=data.get("vector", []),
            text=data.get("text", ""),
            entity_type=data.get("entity_type", "general"),
            cleaned_record=data.get("cleaned_record", {}),
            original_record=data.get("original_record", {}),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", time.time())
        )


class VectorCollection:
    """Manages an isolated vector collection (e.g. customers, stores, items, schemas)."""
    def __init__(self, name: str, persist_dir: str = DB_DIR):
        self.name = name
        self.persist_dir = persist_dir
        self.file_path = os.path.join(self.persist_dir, f"{name}.json")
        self.documents: Dict[str, VectorDocument] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Loads persisted documents from disk if file exists."""
        if not os.path.exists(self.persist_dir):
            os.makedirs(self.persist_dir, exist_ok=True)
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        doc = VectorDocument.from_dict(item)
                        self.documents[doc.doc_id] = doc
            except Exception as e:
                print(f"[VectorCollection:{self.name}] Error loading disk index: {e}")

    def persist(self) -> None:
        """Saves current collection state to disk."""
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([doc.to_dict() for doc in self.documents.values()], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[VectorCollection:{self.name}] Error saving disk index: {e}")

    def upsert(self, doc: VectorDocument, auto_persist: bool = True) -> None:
        """Inserts or updates a single document."""
        self.documents[doc.doc_id] = doc
        if auto_persist:
            self.persist()

    def upsert_batch(self, docs: List[VectorDocument]) -> None:
        """Inserts or updates a batch of documents and persists once."""
        for doc in docs:
            self.documents[doc.doc_id] = doc
        self.persist()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        min_score: float = 0.20,
        filter_fn: Optional[Any] = None
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Performs cosine similarity search against all documents in this collection.
        Returns sorted list of (document, similarity_score) pairs.
        """
        if not self.documents or not query_vector:
            return []

        doc_list = list(self.documents.values())
        if filter_fn:
            doc_list = [d for d in doc_list if filter_fn(d)]

        if not doc_list:
            return []

        # Vectorized cosine similarity computation
        doc_matrix = np.array([d.vector for d in doc_list], dtype=np.float32)
        q_vec = np.array(query_vector, dtype=np.float32)

        # Dot product with unit vectors gives cosine similarity
        scores = np.dot(doc_matrix, q_vec)

        results: List[Tuple[VectorDocument, float]] = []
        for idx, score in enumerate(scores):
            f_score = float(score)
            if f_score >= min_score:
                results.append((doc_list[idx], f_score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def count(self) -> int:
        return len(self.documents)

    def clear(self) -> None:
        self.documents.clear()
        self.persist()


class VectorStoreManager:
    """Singleton Vector Store managing all entity and schema collections."""
    _instance: Optional[VectorStoreManager] = None

    def __init__(self):
        self.collections: Dict[str, VectorCollection] = {
            "customer": VectorCollection("customer_knowledge"),
            "store": VectorCollection("store_knowledge"),
            "item": VectorCollection("item_knowledge"),
            "transaction": VectorCollection("transaction_knowledge"),
            "schema": VectorCollection("schema_knowledge"),
            "general": VectorCollection("general_knowledge")
        }

    @classmethod
    def get_instance(cls) -> VectorStoreManager:
        if cls._instance is None:
            cls._instance = VectorStoreManager()
        return cls._instance

    def get_collection(self, entity_type: str) -> VectorCollection:
        key = entity_type.lower().strip()
        if key in self.collections:
            return self.collections[key]
        # Map common aliases
        if key in ("product", "products", "items"):
            return self.collections["item"]
        if key in ("stores", "branch", "branches"):
            return self.collections["store"]
        if key in ("customers", "client", "user"):
            return self.collections["customer"]
        if key in ("transactions", "orders", "sales"):
            return self.collections["transaction"]
        return self.collections["general"]


def get_vector_collection(entity_type: str) -> VectorCollection:
    """Public helper to get the collection for an entity type."""
    return VectorStoreManager.get_instance().get_collection(entity_type)
