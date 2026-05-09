"""Python code analysis and symbol extraction using AST."""

from typing import List, Optional
import ast
import logging
from pathlib import Path

from .base import BaseParser, CodeSymbol

logger = logging.getLogger(__name__)

class PythonParser(BaseParser):
    """Extract symbols from Python code for indexing."""

    def parse_file(self, file_path: Path) -> List[CodeSymbol]:
        """Extract symbols from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except Exception as e:
            logger.warning(f"Cannot read {file_path}: {e}")
            return []

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return []

        # Find imports at file level
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        symbols = []
        lines = source.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbol = self._extract_function(node, file_path, lines, imports)
                if symbol:
                    symbols.append(symbol)
            elif isinstance(node, ast.ClassDef):
                symbol = self._extract_class(node, file_path, lines, imports)
                if symbol:
                    symbols.append(symbol)

        return symbols

    def __init__(self, workspace_root: Optional[Path] = None):
        """Initialize code analyzer."""
        self.workspace_root = workspace_root or Path.cwd()

    def analyze_workspace(self) -> List[CodeSymbol]:
        """Analyze all Python files in workspace."""
        symbols = []
        python_files = list(self.workspace_root.rglob('*.py'))

        logger.info(f"Found {len(python_files)} Python files")

        for file_path in python_files:
            # Skip common directories
            if any(part in file_path.parts for part in ['.venv', 'venv', '__pycache__', '.git']):
                continue

            try:
                file_symbols = self.parse_file(file_path)
                symbols.extend(file_symbols)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")

        return symbols


    def _extract_function(self, node: ast.FunctionDef, file_path: Path, lines: List[str], imports: List[str]) -> Optional[CodeSymbol]:
        """Extract function symbol."""
        name = node.name
        signature = self._get_signature(node)
        docstring = ast.get_docstring(node) or ""
        line_number = node.lineno

        symbol_id = f"{file_path.stem}::{name}::{line_number}"

        # Extract body (up to 500 chars)
        end_line = min(node.end_lineno or line_number + 10, len(lines))
        body = '\n'.join(lines[line_number - 1:end_line])[:500]

        # Extract calls
        calls = []
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                if isinstance(subnode.func, ast.Name):
                    calls.append(subnode.func.id)
                elif isinstance(subnode.func, ast.Attribute):
                    calls.append(subnode.func.attr)

        return CodeSymbol(
            id=symbol_id,
            name=name,
            symbol_type='function',
            file_path=file_path,
            line_number=line_number,
            signature=signature,
            docstring=docstring,
            body=body,
            external_calls=list(set(calls)),
            external_imports=imports
        )

    def _extract_class(self, node: ast.ClassDef, file_path: Path, lines: List[str], imports: List[str]) -> Optional[CodeSymbol]:
        """Extract class symbol."""
        name = node.name
        bases = ', '.join([self._node_to_str(base) for base in node.bases])
        signature = f"class {name}({bases})" if bases else f"class {name}"
        docstring = ast.get_docstring(node) or ""
        line_number = node.lineno

        symbol_id = f"{file_path.stem}::{name}::{line_number}"

        # Extract body
        end_line = min(node.end_lineno or line_number + 10, len(lines))
        body = '\n'.join(lines[line_number - 1:end_line])[:500]

        # Extract symbols within class (methods) that call things
        calls = []
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                if isinstance(subnode.func, ast.Name):
                    calls.append(subnode.func.id)
                elif isinstance(subnode.func, ast.Attribute):
                    calls.append(subnode.func.attr)

        return CodeSymbol(
            id=symbol_id,
            name=name,
            symbol_type='class',
            file_path=file_path,
            line_number=line_number,
            signature=signature,
            docstring=docstring,
            body=body,
            external_calls=list(set(calls)),
            external_imports=imports
        )

    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature."""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)

        return f"def {node.name}({', '.join(args)})"

    def _node_to_str(self, node: ast.expr) -> str:
        """Convert AST node to string."""
        if isinstance(node, ast.Name):
            return node.id
        return ""
