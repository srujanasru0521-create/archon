from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional
from pathlib import Path

class CodeSymbol(NamedTuple):
    """Represents a code symbol (function, class, variable)."""
    id: str  # Unique identifier
    name: str
    symbol_type: str  # 'function', 'class', 'method', 'variable'
    file_path: Path
    line_number: int
    signature: str  # Function/class signature
    docstring: str  # Documentation
    body: str  # Source code
    external_calls: List[str] = [] # Names of symbols called
    external_imports: List[str] = [] # Names of modules/symbols imported

class BaseParser(ABC):
    """Base interface for language parsers."""
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> List[CodeSymbol]:
        """Extract symbols and rudimentary relationships from a single file."""
        pass
