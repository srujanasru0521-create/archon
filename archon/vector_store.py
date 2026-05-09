"""Vector store for code symbol embeddings with efficient retrieval."""

from typing import Dict, List, Tuple, Optional
import numpy as np
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStore:
    """Store and retrieve embeddings using FAISS-like approach."""

    def __init__(self, embedding_dim: int = 384):
        """Initialize vector store."""
        self.embedding_dim = embedding_dim
        self.index = {}  # symbol_id -> embedding
        self.metadata = {}  # symbol_id -> metadata
        self.embeddings = np.zeros((0, embedding_dim), dtype=np.float32)

    def add_embedding(
        self,
        symbol_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> None:
        """Add single embedding."""
        if embedding.shape != (self.embedding_dim,):
            raise ValueError(f"Expected embedding shape ({self.embedding_dim},), got {embedding.shape}")

        self.index[symbol_id] = len(self.embeddings)
        self.metadata[symbol_id] = metadata or {}

        # Store embedding
        self.embeddings = np.vstack([self.embeddings, embedding.reshape(1, -1)])

    def add_batch(
        self,
        symbol_ids: List[str],
        embeddings: np.ndarray,
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """Batch add embeddings."""
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Expected embedding dim {self.embedding_dim}, got {embeddings.shape[1]}")

        if metadatas is None:
            metadatas = [{} for _ in symbol_ids]

        for i, (sid, embedding, metadata) in enumerate(zip(symbol_ids, embeddings, metadatas)):
            self.index[sid] = len(self.embeddings) + i
            self.metadata[sid] = metadata

        self.embeddings = np.vstack([self.embeddings, embeddings])

    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """
        Find k nearest neighbors using cosine similarity.

        Returns:
            List of (symbol_id, similarity_score) tuples
        """
        if len(self.embeddings) == 0:
            return []

        # Compute cosine similarities
        query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        similarities = np.dot(self.embeddings, query_embedding)

        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_indices:
            symbol_id = list(self.index.keys())[list(self.index.values()).index(idx)]
            results.append((symbol_id, float(similarities[idx])))

        return results

    def save(self, path: Path) -> None:
        """Persist vector store to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'embeddings': self.embeddings.tolist(),
            'index': self.index,
            'metadata': self.metadata,
            'embedding_dim': self.embedding_dim
        }

        with open(path, 'w') as f:
            json.dump(data, f)

        logger.info(f"✓ Saved {len(self.index)} embeddings to {path}")

    def load(self, path: Path) -> None:
        """Load vector store from disk."""
        with open(path, 'r') as f:
            data = json.load(f)

        self.embeddings = np.array(data['embeddings'], dtype=np.float32)
        self.index = data['index']
        self.metadata = data['metadata']
        self.embedding_dim = data['embedding_dim']

        logger.info(f"✓ Loaded {len(self.index)} embeddings from {path}")
