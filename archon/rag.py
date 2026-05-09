"""Retrieval-Augmented Generation system for code understanding."""

from typing import List, NamedTuple, Optional
import logging
from pathlib import Path

from .parsers.python_parser import PythonParser
from .parsers.base import CodeSymbol
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .graph import CodeGraph

logger = logging.getLogger(__name__)


class RAGResult(NamedTuple):
    """Result from RAG retrieval."""
    symbol_id: str
    name: str
    signature: str
    docstring: str
    file_path: str
    similarity: float


class CodeRAG:
    """Retrieval-Augmented Generation for code understanding."""

    def __init__(self, workspace_root: Optional[Path] = None):
        """Initialize RAG system."""
        self.workspace_root = workspace_root or Path.cwd()
        
        # Setup .ai_context directory
        self.context_dir = self.workspace_root / ".ai_context"
        self.context_dir.mkdir(exist_ok=True)
        
        self.parser = PythonParser(self.workspace_root)
        self.embeddings = EmbeddingGenerator()
        
        # Persistent storage paths
        self.graph_path = self.context_dir / "graph.db"
        self.vector_path = self.context_dir / "index.json"
        
        self.graph = CodeGraph(db_path=self.graph_path)
        self.vector_store = VectorStore()
        
        # Try to load existing index
        if self.vector_path.exists():
            try:
                self.vector_store.load(self.vector_path)
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                
        self.symbol_map = {}  # symbol_id -> CodeSymbol

    def index_workspace(self) -> None:
        """Index all Python files in workspace with relationship resolution."""
        logger.info(f"Building intelligence layer in {self.context_dir}...")
        symbols = self.parser.analyze_workspace()

        logger.info(f"Pass 1: Generating embeddings for {len(symbols)} symbols...")
        embeddings_dict = self.embeddings.embed_batch(symbols)

        # Clear existing graph if re-indexing full workspace
        self.graph.clear()

        # Map for resolving calls: name -> symbol_id
        name_to_id = {}
        for symbol in symbols:
            name_to_id[symbol.name] = symbol.id

        # Add to vector store and graph
        for symbol in symbols:
            embedding = embeddings_dict[symbol.id]
            metadata = {
                'name': symbol.name,
                'type': symbol.symbol_type,
                'file': str(symbol.file_path),
                'line': symbol.line_number,
                'signature': symbol.signature,
                'docstring': symbol.docstring
            }
            # Update Vector Store
            self.vector_store.add_embedding(symbol.id, embedding, metadata)
            self.symbol_map[symbol.id] = symbol
            
            # Update Knowledge Graph
            self.graph.add_symbol(
                symbol_id=symbol.id,
                name=symbol.name,
                symbol_type=symbol.symbol_type,
                file_path=str(symbol.file_path),
                line_number=symbol.line_number,
                signature=symbol.signature,
                docstring=symbol.docstring
            )

        logger.info("Pass 2: Resolving relationships...")
        rel_count = 0
        for symbol in symbols:
            # Resolve calls
            for call_name in symbol.external_calls:
                if call_name in name_to_id:
                    target_id = name_to_id[call_name]
                    if target_id != symbol.id:
                        self.graph.add_relationship(symbol.id, target_id, "calls")
                        rel_count += 1
            
            # Resolve imports (simple version: match module name to file stem)
            for imp in symbol.external_imports:
                stem = imp.split('.')[-1]
                # If we have any symbol from that file, link it
                for sid, target in self.symbol_map.items():
                    if Path(target.file_path).stem == stem:
                        self.graph.add_relationship(symbol.id, sid, "imports")
                        rel_count += 1
                        break

        # Auto-save index
        self.save_index(self.vector_path)
        logger.info(f"✓ Indexed {len(symbols)} symbols and {rel_count} relationships")
        
        # Run Sentry checks
        from .sentry import ConstraintChecker
        sentry = ConstraintChecker(self.workspace_root, self.graph)
        violations = sentry.check_constraints()
        if violations:
            logger.warning(f"⚠️ Architecture Sentry found {len(violations)} guardrail violations!")
            for v in violations:
                logger.warning(f"  - {v.source_name} -> {v.target_name} violates ({v.constraint})")
        else:
            logger.info("✓ Sentry passing. No architectural violations.")

    def index_file(self, file_path: Path) -> None:
        """Index a single Python file."""
        logger.info(f"Re-indexing {file_path}...")
        symbols = self.parser.parse_file(file_path)
        
        if not symbols:
            return
            
        embeddings_dict = self.embeddings.embed_batch(symbols)
        
        # Add updated symbols to vector store and graph
        for symbol in symbols:
            embedding = embeddings_dict[symbol.id]
            metadata = {
                'name': symbol.name,
                'type': symbol.symbol_type,
                'file': str(symbol.file_path),
                'line': symbol.line_number,
                'signature': symbol.signature,
                'docstring': symbol.docstring
            }
            # Update Vector Store
            self.vector_store.add_embedding(symbol.id, embedding, metadata)
            self.symbol_map[symbol.id] = symbol
            
            # Update Knowledge Graph
            self.graph.add_symbol(
                symbol_id=symbol.id,
                name=symbol.name,
                symbol_type=symbol.symbol_type,
                file_path=str(symbol.file_path),
                line_number=symbol.line_number,
                signature=symbol.signature,
                docstring=symbol.docstring
            )
            
        # Auto-save index after single file update
        self.save_index(self.vector_path)
        logger.info(f"✓ Updated {len(symbols)} symbols from {file_path.name}")

    def retrieve(self, query: str, k: int = 5) -> List[RAGResult]:
        """
        Retrieve relevant code symbols for a query.

        Args:
            query: Natural language query
            k: Number of results to return

        Returns:
            List of RAGResult with most relevant symbols
        """
        query_embedding = self.embeddings.embed_text(query)
        results = self.vector_store.search(query_embedding, k=k)

        rag_results = []
        for symbol_id, similarity in results:
            metadata = self.vector_store.metadata[symbol_id]

            rag_results.append(RAGResult(
                symbol_id=symbol_id,
                name=metadata['name'],
                signature=metadata['signature'],
                docstring=metadata['docstring'],
                file_path=metadata['file'],
                similarity=similarity
            ))

        return rag_results

    def save_index(self, path: Path) -> None:
        """Persist index to disk."""
        self.vector_store.save(path)
        logger.info(f"✓ Saved RAG index to {path}")

    def load_index(self, path: Path) -> None:
        """Load index from disk."""
        self.vector_store.load(path)
        # Note: Symbol map not persisted, only embeddings
        logger.info(f"✓ Loaded RAG index from {path}")


def create_rag_prompt(query: str, retrieved: List[RAGResult]) -> str:
    """
    Create a prompt with retrieved context for LLM.

    Args:
        query: Original user query
        retrieved: List of retrieved symbols

    Returns:
        Formatted prompt with context
    """
    context = "## Retrieved Code Context\n\n"

    for result in retrieved:
        context += f"### {result.name} (similarity: {result.similarity:.2f})\n"
        context += f"**File:** {result.file_path}\n"
        context += f"**Signature:** `{result.signature}`\n"
        if result.docstring:
            context += f"**Documentation:** {result.docstring}\n"
        context += "\n"

    prompt = f"""Based on the following code context, answer the question:

{context}

**Question:** {query}

**Answer:**"""

    return prompt
