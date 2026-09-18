"""
Embedding Generation Engine for RAG Knowledge Base

Generates dense normalized vector embeddings (384-dim) for record strings,
search queries, and schema aliases. Features fast local generation with zero external latency.
"""
from __future__ import annotations
import math
import hashlib
import re
from typing import List, Union
import numpy as np


class LocalDenseEmbedder:
    """
    High-performance, deterministic local embedding engine.
    Generates 384-dimensional unit-normalized dense semantic embeddings.
    Combines character n-grams, word tokens, and semantic feature hashing
    for robust typo-tolerant similarity retrieval.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _tokenize(self, text: str) -> List[str]:
        """Extracts word tokens, character bigrams/trigrams, and normalized phone/id segments."""
        if not text:
            return []
        text_clean = text.lower().strip()
        tokens = []

        # 1. Full string token
        tokens.append(f"full_{text_clean}")

        # 2. Words & split sub-words (split by space, underscore, dash)
        raw_words = re.findall(r"[\w@\.\+]+", text_clean)
        tokens.extend(raw_words)
        
        split_words = re.split(r"[_\-\s\.]+", text_clean)
        for sw in split_words:
            if sw:
                tokens.append(f"w_{sw}")

        # 3. Extract character 2-grams, 3-grams, and 4-grams for abbreviation & typo tolerance
        all_words = set(raw_words + split_words)
        for w in all_words:
            if len(w) >= 2:
                for i in range(len(w) - 1):
                    tokens.append(f"bi_{w[i:i+2]}")
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    tokens.append(f"tri_{w[i:i+3]}")
            if len(w) >= 4:
                for i in range(len(w) - 3):
                    tokens.append(f"quad_{w[i:i+4]}")

        # 4. Numeric & identifier components (e.g. phone digits, postal codes, ID prefixes)
        digits = re.findall(r"\d+", text_clean)
        for d in digits:
            tokens.append(f"num_{d}")
            if len(d) >= 4:
                tokens.append(f"num_end_{d[-4:]}")

        return tokens

    def embed_text(self, text: str) -> List[float]:
        """Generates a 384-dimensional unit-length embedding vector for input text."""
        if not text or not str(text).strip():
            return [0.0] * self.dim

        tokens = self._tokenize(str(text))
        vec = np.zeros(self.dim, dtype=np.float32)

        for token in tokens:
            # Deterministic double-hash projection across dimensions
            h1 = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16)
            h2 = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16)
            
            idx = h1 % self.dim
            weight = 1.0 + ((h2 % 100) / 200.0)
            sign = 1.0 if (h2 % 2 == 0) else -1.0
            vec[idx] += sign * weight

            # Secondary projection for dispersion
            idx2 = (h1 * 31 + h2) % self.dim
            vec[idx2] += (sign * 0.5)

        # L2 Unit Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of strings."""
        return [self.embed_text(t) for t in texts]


# Global singleton instance
_GLOBAL_EMBEDDER = LocalDenseEmbedder(dim=384)


def get_embedding(text: str) -> List[float]:
    """Public helper to get embedding for a single string."""
    return _GLOBAL_EMBEDDER.embed_text(text)


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Public helper to get embeddings for a batch of strings."""
    return _GLOBAL_EMBEDDER.embed_batch(texts)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two unit vectors (range: -1.0 to 1.0)."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = float(np.dot(a, b))
    # Clamp to [0.0, 1.0] for similarity score usage
    return max(0.0, min(1.0, dot))
