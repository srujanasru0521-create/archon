"""Generate embeddings for code symbols using sentence-transformers."""

from typing import Dict, List
import numpy as np
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for code symbols."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding generator.

        Args:
            model_name: sentence-transformers model to use
        """
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {model_name}...")
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = 384
            logger.info("✓ Embedding model loaded")

        except ImportError:
            logger.error("sentence-transformers not installed")
            raise

    def embed_symbol(self, symbol) -> np.ndarray:
        """
        Create embedding for a single symbol.

        Args:
            symbol: CodeSymbol object

        Returns:
            384-dimensional normalized embedding
        """
        text = f"{symbol.name}\n{symbol.signature}\n{symbol.docstring}\n{symbol.body[:300]}"

        embedding = self.model.encode(text, normalize_embeddings=True)
        return np.array(embedding, dtype=np.float32)

    def embed_batch(self, symbols: List) -> Dict[str, np.ndarray]:
        """
        Batch embed multiple symbols efficiently.

        Args:
            symbols: List of CodeSymbol objects

        Returns:
            Dictionary mapping symbol ID to embedding
        """
        if not symbols:
            return {}

        texts = [
            f"{s.name}\n{s.signature}\n{s.docstring}\n{s.body[:300]}"
            for s in symbols
        ]

        logger.info(f"Embedding {len(symbols)} symbols...")
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=True
        )
        logger.info(f"✓ Embedded {len(symbols)} symbols")

        return {s.id: np.array(embeddings[i], dtype=np.float32) for i, s in enumerate(symbols)}

    def embed_text(self, text: str) -> np.ndarray:
        """Embed any text query."""
        return np.array(
            self.model.encode(text, normalize_embeddings=True),
            dtype=np.float32
        )
