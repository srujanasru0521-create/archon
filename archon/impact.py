import logging
from typing import List, Dict, Set
from .graph import CodeGraph

logger = logging.getLogger(__name__)

class BlastRadiusCalculator:
    """Calculates exactly what will break if a component is modified."""

    def __init__(self, graph: CodeGraph):
        self.graph = graph

    def calculate_impact(self, target_id: str) -> Dict[str, dict]:
        """
        Recursively trace all downstream dependencies to calculate
        the blast radius of modifying `target_id`.
        """
        affected = {}
        visited = set()

        def trace(node_id: str, depth: int):
            if depth > 10 or node_id in visited:
                return
            visited.add(node_id)
            
            # Find symbols that import or call this node_id
            callers = self.graph.get_incoming_relationships(node_id)
            for caller_id, rel_type in callers:
                caller_symbol = self.graph.get_symbol(caller_id)
                if not caller_symbol:
                    continue
                
                if caller_id not in affected:
                    affected[caller_id] = {
                        'name': caller_symbol['name'],
                        'type': caller_symbol['type'],
                        'file_path': caller_symbol['file_path'],
                        'depth': depth,
                        'impacted_by': [node_id]
                    }
                else:
                    if node_id not in affected[caller_id]['impacted_by']:
                        affected[caller_id]['impacted_by'].append(node_id)
                
                trace(caller_id, depth + 1)
        
        # Start trace from target_id or resolve by name
        target_symbol = self.graph.get_symbol(target_id)
        if not target_symbol:
            # Try finding by name
            with __import__('sqlite3').connect(self.graph.db_path) as conn:
                cursor = conn.execute("SELECT id FROM symbols WHERE name = ? LIMIT 1", (target_id,))
                row = cursor.fetchone()
                if row:
                    target_id = row[0]
                    target_symbol = self.graph.get_symbol(target_id)
                else:
                    raise ValueError(f"Symbol '{target_id}' not found in the graph.")

        trace(target_id, 1)

        # Remove the target itself if it accidentally looped in
        if target_id in affected:
            del affected[target_id]

        return affected
