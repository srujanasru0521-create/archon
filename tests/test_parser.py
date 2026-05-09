"""Test parser functionality."""

import tempfile
from pathlib import Path
import sys
import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pcil.parser import PythonParser, CodeSymbol


def test_parse_simple_function():
    """Test parsing a simple function."""
    parser = PythonParser()

    code = """
def calculate_total(items):
    '''Calculate total price.'''
    return sum(item.price for item in items)
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()

        symbols = parser.parse(f.name)

        assert len(symbols) > 0
        assert any(s.name == "calculate_total" for s in symbols)

        Path(f.name).unlink()


def test_parse_class():
    """Test parsing a class."""
    parser = PythonParser()

    code = """
class Order:
    '''Order class.'''
    def process(self):
        return True
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()

        symbols = parser.parse(f.name)

        assert any(s.name == "Order" for s in symbols)

        Path(f.name).unlink()


def test_parse_dependencies():
    """Test extracting function calls."""
    parser = PythonParser()

    code = """
def foo():
    return bar()

def bar():
    return True
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()

        symbols = parser.parse(f.name)
        foo_symbol = next((s for s in symbols if s.name == "foo"), None)

        assert foo_symbol is not None
        assert "bar" in foo_symbol.dependencies

        Path(f.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
