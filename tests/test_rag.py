"""Tests for RAG components."""

import pytest
from pathlib import Path
import tempfile
import numpy as np

from pcil import (
    CodeAnalyzer, CodeSymbol, EmbeddingGenerator, 
    VectorStore, CodeRAG, create_rag_prompt
)


class TestCodeAnalyzer:
    """Tests for code symbol extraction."""
    
    def test_extract_function(self):
        """Test function extraction."""
        code = '''
def add(a, b):
    """Add two numbers."""
    return a + b
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            analyzer = CodeAnalyzer()
            symbols = analyzer.analyze_file(Path(f.name))
            
            assert len(symbols) == 1
            assert symbols[0].name == "add"
            assert symbols[0].symbol_type == "function"
            assert "Add two numbers" in symbols[0].docstring
    
    def test_extract_class(self):
        """Test class extraction."""
        code = '''
class Calculator:
    """A simple calculator."""
    
    def add(self, a, b):
        return a + b
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            analyzer = CodeAnalyzer()
            symbols = analyzer.analyze_file(Path(f.name))
            
            # Should find both class and method
            class_symbols = [s for s in symbols if s.symbol_type == "class"]
            assert len(class_symbols) >= 1


class TestEmbeddingGenerator:
    """Tests for embedding generation."""
    
    def test_embedding_dimension(self):
        """Test that embeddings have correct dimension."""
        generator = EmbeddingGenerator()
        text = "This is a test sentence"
        embedding = generator.embed_text(text)
        
        assert embedding.shape == (384,)
        assert isinstance(embedding, np.ndarray)
    
    def test_normalized_embeddings(self):
        """Test that embeddings are normalized."""
        generator = EmbeddingGenerator()
        text = "Test sentence for normalization"
        embedding = generator.embed_text(text)
        
        # Normalized vectors have magnitude close to 1
        magnitude = np.linalg.norm(embedding)
        assert abs(magnitude - 1.0) < 0.01


class TestVectorStore:
    """Tests for vector store operations."""
    
    def test_add_and_search(self):
        """Test adding embeddings and searching."""
        store = VectorStore(embedding_dim=384)
        
        # Create test embeddings
        embedding1 = np.random.randn(384)
        embedding1 /= np.linalg.norm(embedding1)
        
        # Create a slightly different embedding
        embedding2 = embedding1 + np.random.randn(384) * 0.1
        embedding2 /= np.linalg.norm(embedding2)
        
        embedding3 = np.random.randn(384)
        embedding3 /= np.linalg.norm(embedding3)
        
        store.add_embedding("symbol1", embedding1, {"name": "symbol1"})
        store.add_embedding("symbol2", embedding2, {"name": "symbol2"})
        store.add_embedding("symbol3", embedding3, {"name": "symbol3"})
        
        # Search with query similar to embedding1
        results = store.search(embedding1, k=2)
        
        assert len(results) == 2
        # Top result should be symbol1 (exact match)
        assert results[0][0] == "symbol1"
        # Results should be ranked by similarity
        assert results[0][1] >= results[1][1] - 0.01  # Allow small floating point errors
    
    def test_persist_and_load(self):
        """Test saving and loading vector store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store.json"
            
            # Create and save store
            store1 = VectorStore()
            embedding = np.random.randn(384)
            embedding /= np.linalg.norm(embedding)
            store1.add_embedding("test", embedding, {"name": "test"})
            store1.save(store_path)
            
            # Load store
            store2 = VectorStore()
            store2.load(store_path)
            
            assert len(store2.index) == 1
            assert "test" in store2.index
            assert store2.metadata["test"]["name"] == "test"


class TestCodeRAG:
    """Tests for RAG system."""
    
    def test_rag_retrieval(self):
        """Test RAG retrieval on sample code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample Python file
            code = '''
def process_data(data):
    """Process input data and return results."""
    return [x * 2 for x in data]

def validate_input(data):
    """Validate that input is not empty."""
    return len(data) > 0

class DataProcessor:
    """Main data processing class."""
    
    def run(self, data):
        """Execute the processing pipeline."""
        if validate_input(data):
            return process_data(data)
'''
            code_file = Path(tmpdir) / "sample.py"
            code_file.write_text(code)
            
            # Create and index RAG
            rag = CodeRAG(Path(tmpdir))
            rag.index_workspace()
            
            # Test retrieval
            results = rag.retrieve("process data", k=2)
            
            assert len(results) > 0
            assert any("process" in r.name.lower() for r in results)
    
    def test_rag_prompt_generation(self):
        """Test RAG prompt generation."""
        from pcil import RAGResult
        
        results = [
            RAGResult(
                symbol_id="test1",
                name="test_function",
                signature="def test_function():",
                docstring="A test function",
                file_path="test.py",
                similarity=0.95
            ),
            RAGResult(
                symbol_id="test2",
                name="test_class",
                signature="class TestClass:",
                docstring="A test class",
                file_path="test.py",
                similarity=0.85
            )
        ]
        
        prompt = create_rag_prompt("How to use this code?", results)
        
        assert "test_function" in prompt
        assert "test_class" in prompt
        assert "test.py" in prompt
        assert "How to use this code?" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
