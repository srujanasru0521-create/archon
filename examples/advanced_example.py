#!/usr/bin/env python3
"""Example: Graph Database and API Usage"""

from pathlib import Path
from pcil import CodeRAG, CodeGraph
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_graph_db():
    """Example: Using the code graph database."""
    
    print("\n" + "="*70)
    print("📊 CODE GRAPH DATABASE EXAMPLE")
    print("="*70 + "\n")
    
    # Initialize graph
    graph = CodeGraph(db_path=Path("./code_graph.db"))
    
    # Add some sample symbols
    symbols = [
        ("app::main", "main", "function", "app.py", 1, "def main():", "Main entry point"),
        ("app::init_db", "init_db", "function", "app.py", 5, "def init_db():", "Initialize database"),
        ("app::DataProcessor", "DataProcessor", "class", "app.py", 10, "class DataProcessor:", "Data processor class"),
        ("app::process_data", "process_data", "method", "app.py", 15, "def process_data(self):", "Process data"),
    ]
    
    for sym_id, name, sym_type, file_path, line, sig, doc in symbols:
        graph.add_symbol(sym_id, name, sym_type, file_path, line, sig, doc)
    
    # Add relationships
    relationships = [
        ("app::main", "app::init_db", "calls"),  # main calls init_db
        ("app::main", "app::DataProcessor", "uses"),  # main uses DataProcessor
        ("app::DataProcessor", "app::process_data", "contains"),  # class contains method
        ("app::process_data", "app::init_db", "calls"),  # method calls init_db
    ]
    
    for source, target, rel_type in relationships:
        graph.add_relationship(source, target, rel_type)
    
    print("✓ Graph created with 4 symbols and 4 relationships\n")
    
    # Query relationships
    print("🔍 Functions called by main():")
    for target, rel_type in graph.get_outgoing_relationships("app::main"):
        symbol = graph.get_symbol(target)
        print(f"  → {symbol['name']} ({rel_type})")
    
    print("\n🔍 What calls init_db():")
    for source, rel_type in graph.get_incoming_relationships("app::init_db"):
        symbol = graph.get_symbol(source)
        print(f"  ← {symbol['name']} ({rel_type})")
    
    # Get dependency chain
    print("\n📈 Dependency chain for main():")
    chain = graph.get_dependency_chain("app::main", max_depth=2)
    for sid, info in chain.items():
        symbol = info['symbol']
        depth = info['depth']
        print(f"  {'  '*depth}└─ {symbol['name']} (depth: {depth})")
        for dep in info['depends_on']:
            dep_sym = graph.get_symbol(dep['id'])
            print(f"  {'  '*(depth+1)}→ {dep_sym['name']} ({dep['type']})")
    
    # Get statistics
    print("\n📊 Graph Statistics:")
    stats = graph.get_statistics()
    print(f"  Total symbols: {stats['total_symbols']}")
    print(f"  Total relationships: {stats['total_relationships']}")
    print(f"  Relationship types: {stats['relationship_types']}")
    
    # Save visualization
    viz_path = Path("./graph_visualization.json")
    graph.save_visualization(viz_path)
    print(f"\n✓ Graph visualization saved to: {viz_path}")


def example_with_rag_and_graph():
    """Example: Combining RAG and Graph DB for complete analysis."""
    
    print("\n" + "="*70)
    print("🔗 COMBINING RAG + GRAPH DB")
    print("="*70 + "\n")
    
    # Index code with RAG
    rag = CodeRAG(workspace_root=Path.cwd())
    print("📚 Indexing workspace...")
    rag.index_workspace()
    print(f"✓ Indexed {len(rag.vector_store.index)} symbols\n")
    
    # Initialize graph for the same codebase
    graph = CodeGraph(db_path=Path("./combined_graph.db"))
    
    # Add all indexed symbols to graph
    print("📊 Building relationship graph...")
    for symbol_id, metadata in rag.vector_store.metadata.items():
        graph.add_symbol(
            symbol_id,
            metadata.get('name', 'unknown'),
            metadata.get('type', 'unknown'),
            metadata.get('file', 'unknown'),
            metadata.get('line', 0),
            metadata.get('signature', ''),
            metadata.get('docstring', '')
        )
    
    print(f"✓ Added {len(rag.vector_store.metadata)} symbols to graph\n")
    
    # Semantic search with RAG
    query = "data validation"
    print(f"🔍 Semantic search for: '{query}'")
    results = rag.retrieve(query, k=3)
    print(f"✓ Found {len(results)} relevant symbols:")
    for result in results:
        print(f"  - {result.name} ({result.similarity:.0%})")
    
    print("\n" + "✅ RAG + Graph DB integration working!")


def example_circular_dependency_detection():
    """Example: Detect circular dependencies."""
    
    print("\n" + "="*70)
    print("⚠️  CIRCULAR DEPENDENCY DETECTION")
    print("="*70 + "\n")
    
    graph = CodeGraph(db_path=Path("./circular_test.db"))
    
    # Create symbols with circular dependency
    for i in range(3):
        graph.add_symbol(f"module::{i}", f"module_{i}", "module", "file.py", i)
    
    # Create cycle: 0 -> 1 -> 2 -> 0
    graph.add_relationship("module::0", "module::1", "imports")
    graph.add_relationship("module::1", "module::2", "imports")
    graph.add_relationship("module::2", "module::0", "imports")
    
    print("Created cycle: module_0 → module_1 → module_2 → module_0\n")
    
    cycles = graph.find_circular_dependencies()
    
    if cycles:
        print("⚠️  Found circular dependencies:")
        for i, cycle in enumerate(cycles, 1):
            cycle_str = " → ".join(cycle)
            print(f"  Cycle {i}: {cycle_str}")
    else:
        print("✓ No circular dependencies found")


# Run examples
if __name__ == "__main__":
    print("\nPCIL Full-Featured Examples\n")
    
    print("Example 1: Graph Database")
    print("-" * 70)
    example_graph_db()
    
    print("\n\nExample 2: RAG + Graph DB Integration")
    print("-" * 70)
    # example_with_rag_and_graph()  # Commented - requires actual indexing
    
    print("\n\nExample 3: Circular Dependency Detection")
    print("-" * 70)
    example_circular_dependency_detection()
    
    print("\n\n" + "="*70)
    print("✅ All examples completed!")
    print("="*70)
