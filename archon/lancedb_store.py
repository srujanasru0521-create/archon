"""LanceDB integration for large-scale vector storage."""

from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class LanceDBStore:
    """Vector store using LanceDB for scalability."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize LanceDB store."""
        self.db_path = db_path or Path("./vectors.lance")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.table = None
        self.metadata = {}

        try:
            import lancedb
            self.lancedb = lancedb
            self._init_db()
        except ImportError:
            logger.error("lancedb not installed. Install with: pip install lancedb")
            raise

    def _init_db(self):
        """Initialize LanceDB connection."""
        try:
            db = self.lancedb.connect(str(self.db_path))
            logger.info(f"✓ Connected to LanceDB at {self.db_path}")
        except Exception as e:
            logger.error(f"LanceDB initialization error: {e}")
            raise

    def add_embedding(
        self,
        symbol_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> None:
        """Add single embedding to LanceDB."""
        if embedding.dtype != np.float32:
            embedding = np.array(embedding, dtype=np.float32)

        db = self.lancedb.connect(str(self.db_path))

        data = {
            'id': symbol_id,
            'vector': embedding.tolist(),
            **{k: str(v) for k, v in (metadata or {}).items()}
        }

        if self.table is None:
            self.table = db.create_table("embeddings", data=[data], mode="overwrite")
        else:
            self.table.add([data])

        self.metadata[symbol_id] = metadata or {}

    def add_batch(
        self,
        symbol_ids: List[str],
        embeddings: np.ndarray,
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """Batch add embeddings to LanceDB."""
        if embeddings.dtype != np.float32:
            embeddings = np.array(embeddings, dtype=np.float32)

        if metadatas is None:
            metadatas = [{} for _ in symbol_ids]

        db = self.lancedb.connect(str(self.db_path))

        data = []
        for i, (sid, embedding, metadata) in enumerate(zip(symbol_ids, embeddings, metadatas)):
            data.append({
                'id': sid,
                'vector': embedding.tolist(),
                **{k: str(v) for k, v in metadata.items()}
            })
            self.metadata[sid] = metadata

        if self.table is None:
            self.table = db.create_table("embeddings", data=data, mode="overwrite")
        else:
            self.table.add(data)

        logger.info(f"✓ Added {len(symbol_ids)} embeddings to LanceDB")

    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar embeddings using LanceDB."""
        if self.table is None:
            return []

        if query_embedding.dtype != np.float32:
            query_embedding = np.array(query_embedding, dtype=np.float32)

        try:
            results = self.table.search(query_embedding.tolist()).limit(k).to_list()

            output = []
            for result in results:
                symbol_id = result['id']
                # LanceDB returns similarity scores, normalize to 0-1 range
                similarity = 1.0 / (1.0 + abs(result.get('_distance', 0)))
                output.append((symbol_id, similarity))

            return output
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def delete_embedding(self, symbol_id: str) -> None:
        """Delete embedding by ID."""
        if self.table is None:
            return

        try:
            self.table.delete(f"id = '{symbol_id}'")
            if symbol_id in self.metadata:
                del self.metadata[symbol_id]
            logger.info(f"✓ Deleted embedding: {symbol_id}")
        except Exception as e:
            logger.error(f"Delete error: {e}")

    def update_embedding(
        self,
        symbol_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> None:
        """Update embedding."""
        self.delete_embedding(symbol_id)
        self.add_embedding(symbol_id, embedding, metadata)

    def get_stats(self) -> Dict:
        """Get database statistics."""
        if self.table is None:
            return {'total_embeddings': 0}

        try:
            count = len(self.table.to_pandas())
            return {
                'total_embeddings': count,
                'total_metadata': len(self.metadata),
                'db_path': str(self.db_path)
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}

    def close(self) -> None:
        """Close database connection."""
        self.table = None
        logger.info("✓ LanceDB connection closed")


class HybridVectorStore:
    """Hybrid store supporting both in-memory and LanceDB."""

    def __init__(self, backend: str = "memory", db_path: Optional[Path] = None):
        """Initialize hybrid store.

        Args:
            backend: "memory" or "lancedb"
            db_path: Path for LanceDB
        """
        self.backend = backend

        if backend == "lancedb":
            self.store = LanceDBStore(db_path or Path("./vectors.lance"))
        else:
            # Fall back to in-memory VectorStore
            from .vector_store import VectorStore
            self.store = VectorStore()

    def add_embedding(self, symbol_id: str, embedding: np.ndarray, metadata=None):
        """Add embedding (backend agnostic)."""
        self.store.add_embedding(symbol_id, embedding, metadata)

    def add_batch(self, symbol_ids, embeddings, metadatas=None):
        """Batch add (backend agnostic)."""
        self.store.add_batch(symbol_ids, embeddings, metadatas)

    def search(self, query_embedding, k=10):
        """Search (backend agnostic)."""
        return self.store.search(query_embedding, k)

    def get_stats(self):
        """Get statistics."""
        if hasattr(self.store, 'get_stats'):
            return self.store.get_stats()
        return {'total_embeddings': len(self.store.index)}
