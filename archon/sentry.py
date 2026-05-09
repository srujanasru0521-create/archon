import logging
from pathlib import Path
from typing import List, Dict

from .config import load_config
from .graph import CodeGraph

logger = logging.getLogger(__name__)

class Violation:
    def __init__(self, source_name: str, target_name: str, constraint: str, rel_type: str):
        self.source_name = source_name
        self.target_name = target_name
        self.constraint = constraint
        self.rel_type = rel_type

class ConstraintChecker:
    """Evaluates relationships against architecture intent."""
    
    def __init__(self, workspace_root: Path, graph: CodeGraph):
        self.workspace_root = workspace_root
        self.graph = graph
        self.config = load_config(workspace_root)
        
    def check_constraints(self) -> List[Violation]:
        """Check all relationships against constraints."""
        if not self.config.constraints:
            return []
            
        violations = []
        # get all relationships
        with __import__('sqlite3').connect(self.graph.db_path) as conn:
            cursor = conn.execute("""
                SELECT s1.name, s2.name, s1.file_path, s2.file_path, r.rel_type 
                FROM relationships r
                JOIN symbols s1 ON r.source_id = s1.id
                JOIN symbols s2 ON r.target_id = s2.id
            """)
            relationships = cursor.fetchall()
            
        # Parse forbidden constraints (e.g. "API !-> Storage")
        forbidden_rules = []
        for constraint in self.config.constraints:
            if '!->' in constraint:
                source, target = [p.strip() for p in constraint.split('!->')]
                forbidden_rules.append((source, target, constraint))

        # Map files to layers
        def get_layer(file_path: str) -> str:
            rel_path = Path(file_path).relative_to(self.workspace_root).as_posix()
            for layer in self.config.layers:
                if rel_path.startswith(layer.path) or layer.path in rel_path:
                    return layer.name
            return "Unknown"

        for src_name, tgt_name, src_file, tgt_file, rel_type in relationships:
            src_layer = get_layer(src_file)
            tgt_layer = get_layer(tgt_file)
            
            for f_src, f_tgt, rule_str in forbidden_rules:
                if src_layer == f_src and tgt_layer == f_tgt:
                    violations.append(Violation(src_name, tgt_name, rule_str, rel_type))
                    
        return violations
