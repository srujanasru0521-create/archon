"""Example: Basic RAG Usage"""

from pathlib import Path
import logging

from pcil import CodeRAG, create_rag_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_retrieval():
    """Example: Index code and retrieve relevant symbols."""
    
    # Initialize RAG system for current workspace
    workspace_root = Path.cwd()
    rag = CodeRAG(workspace_root)
    
    # Build index from all Python files
    print("📚 Indexing workspace...")
    rag.index_workspace()
    
    # Example queries
    queries = [
        "How do I handle errors in this codebase?",
        "What functions process data?",
        "Show me authentication-related code",
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 60)
        
        # Retrieve relevant symbols
        results = rag.retrieve(query, k=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.name} ({result.symbol_type})")
            print(f"   File: {result.file_path}")
            print(f"   Similarity: {result.similarity:.2%}")
            print(f"   Signature: {result.signature}")
            if result.docstring:
                # Truncate long docstrings
                doc = result.docstring[:150]
                if len(result.docstring) > 150:
                    doc += "..."
                print(f"   Doc: {doc}")


def example_rag_prompt():
    """Example: Generate RAG-augmented prompts for LLMs."""
    
    rag = CodeRAG(Path.cwd())
    rag.index_workspace()
    
    query = "How should I handle database transactions?"
    
    # Retrieve context
    results = rag.retrieve(query, k=5)
    
    # Create augmented prompt for LLM
    prompt = create_rag_prompt(query, results)
    
    print("🤖 Generated RAG Prompt:")
    print("=" * 70)
    print(prompt)


def example_persistent_index():
    """Example: Save and load index for reuse."""
    
    workspace_root = Path.cwd()
    index_path = Path("./code_index.json")
    
    # First time: build and save index
    if not index_path.exists():
        print("🔨 Building index...")
        rag = CodeRAG(workspace_root)
        rag.index_workspace()
        rag.save_index(index_path)
    else:
        # Load existing index
        print("📂 Loading index...")
        rag = CodeRAG(workspace_root)
        rag.load_index(index_path)
    
    # Use for retrieval
    results = rag.retrieve("configuration management", k=3)
    
    print("\n✨ Retrieved results:")
    for result in results:
        print(f"  - {result.name}: {result.similarity:.2%}")


# Run examples
if __name__ == "__main__":
    print("PCIL RAG Examples\n")
    
    print("Example 1: Basic Retrieval")
    print("=" * 70)
    example_basic_retrieval()
    
    print("\n\nExample 2: Generate RAG Prompt")
    print("=" * 70)
    # example_rag_prompt()  # Commented out for brevity
    
    print("\n\nExample 3: Persistent Index")
    print("=" * 70)
    # example_persistent_index()  # Commented out for brevity
