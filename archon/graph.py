"""Graph database for tracking code relationships using SQLite."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class CodeGraph:
    """Track relationships between code symbols using SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize graph database."""
        self.db_path = db_path or Path("./code_graph.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    signature TEXT,
                    docstring TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    rel_type TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (source_id) REFERENCES symbols(id),
                    FOREIGN KEY (target_id) REFERENCES symbols(id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_source 
                ON relationships(source_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_target 
                ON relationships(target_id)
            """)
            
            conn.commit()
        
        logger.info(f"✓ Graph database initialized at {self.db_path}")

    def add_symbol(
        self,
        symbol_id: str,
        name: str,
        symbol_type: str,
        file_path: str,
        line_number: int,
        signature: str = "",
        docstring: str = ""
    ) -> None:
        """Add a symbol to the graph."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO symbols 
                (id, name, type, file_path, line_number, signature, docstring)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol_id, name, symbol_type, file_path, line_number, signature, docstring))
            conn.commit()

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Add relationship between symbols (calls, imports, inherits, etc)."""
        with sqlite3.connect(self.db_path) as conn:
            metadata_json = json.dumps(metadata or {})
            conn.execute("""
                INSERT INTO relationships (source_id, target_id, rel_type, metadata)
                VALUES (?, ?, ?, ?)
            """, (source_id, target_id, rel_type, metadata_json))
            conn.commit()

    def get_symbol(self, symbol_id: str) -> Optional[Dict]:
        """Get symbol details."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM symbols WHERE id = ?", (symbol_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'file_path': row[3],
                    'line_number': row[4],
                    'signature': row[5],
                    'docstring': row[6]
                }
        return None

    def get_outgoing_relationships(
        self,
        symbol_id: str,
        rel_type: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """Get symbols that this symbol references (calls, imports, etc)."""
        with sqlite3.connect(self.db_path) as conn:
            if rel_type:
                cursor = conn.execute("""
                    SELECT target_id, rel_type FROM relationships
                    WHERE source_id = ? AND rel_type = ?
                """, (symbol_id, rel_type))
            else:
                cursor = conn.execute("""
                    SELECT target_id, rel_type FROM relationships
                    WHERE source_id = ?
                """, (symbol_id,))
            
            return cursor.fetchall()

    def get_incoming_relationships(
        self,
        symbol_id: str,
        rel_type: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """Get symbols that reference this symbol (callers, importers, etc)."""
        with sqlite3.connect(self.db_path) as conn:
            if rel_type:
                cursor = conn.execute("""
                    SELECT source_id, rel_type FROM relationships
                    WHERE target_id = ? AND rel_type = ?
                """, (symbol_id, rel_type))
            else:
                cursor = conn.execute("""
                    SELECT source_id, rel_type FROM relationships
                    WHERE target_id = ?
                """, (symbol_id,))
            
            return cursor.fetchall()

    def get_dependency_chain(self, symbol_id: str, max_depth: int = 3) -> Dict:
        """Get full dependency chain for a symbol."""
        visited = set()
        result = {}

        def traverse(sid: str, depth: int):
            if depth > max_depth or sid in visited:
                return
            visited.add(sid)

            symbol = self.get_symbol(sid)
            if not symbol:
                return

            result[sid] = {
                'symbol': symbol,
                'depends_on': [],
                'depth': depth
            }

            for target_id, rel_type in self.get_outgoing_relationships(sid):
                result[sid]['depends_on'].append({
                    'id': target_id,
                    'type': rel_type
                })
                traverse(target_id, depth + 1)

        traverse(symbol_id, 0)
        return result

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in code."""
        cycles = []
        visited = set()

        def dfs(node: str, path: List[str], rec_stack: set) -> bool:
            visited.add(node)
            path.append(node)
            rec_stack.add(node)

            for target, _ in self.get_outgoing_relationships(node):
                if target not in visited:
                    if dfs(target, path, rec_stack):
                        return True
                elif target in rec_stack:
                    # Found cycle
                    cycle_start = path.index(target)
                    cycles.append(path[cycle_start:] + [target])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT id FROM symbols")
            for (symbol_id,) in cursor:
                if symbol_id not in visited:
                    dfs(symbol_id, [], set())

        return cycles

    def get_statistics(self) -> Dict:
        """Get graph statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM symbols")
            symbol_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM relationships")
            relationship_count = cursor.fetchone()[0]

            cursor = conn.execute("""
                SELECT rel_type, COUNT(*) FROM relationships GROUP BY rel_type
            """)
            rel_types = {row[0]: row[1] for row in cursor}

        return {
            'total_symbols': symbol_count,
            'total_relationships': relationship_count,
            'relationship_types': rel_types
        }

    def clear(self) -> None:
        """Clear the graph database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM relationships")
            conn.execute("DELETE FROM symbols")
            conn.commit()
        logger.info("✓ Graph database cleared")

    def get_central_nodes(self, limit: int = 5) -> List[Dict]:
        """Find nodes with the highest total degree (incoming + outgoing)."""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT id, COUNT(*) as degree
                FROM (
                    SELECT source_id as id FROM relationships
                    UNION ALL
                    SELECT target_id as id FROM relationships
                )
                GROUP BY id
                ORDER BY degree DESC
                LIMIT ?
            """
            cursor = conn.execute(query, (limit,))
            results = []
            for row in cursor:
                symbol = self.get_symbol(row[0])
                if symbol:
                    symbol['degree'] = row[1]
                    results.append(symbol)
            return results

    def get_surprising_connections(self, limit: int = 5) -> List[Dict]:
        """Find relationships that cross between different files (surprising connections)."""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT r.source_id, r.target_id, r.rel_type, s1.file_path, s2.file_path
                FROM relationships r
                JOIN symbols s1 ON r.source_id = s1.id
                JOIN symbols s2 ON r.target_id = s2.id
                WHERE s1.file_path != s2.file_path
                LIMIT ?
            """
            cursor = conn.execute(query, (limit,))
            results = []
            for row in cursor:
                results.append({
                    'source': row[0],
                    'target': row[1],
                    'type': row[2],
                    'source_file': row[3],
                    'target_file': row[4]
                })
            return results

    def save_visualization(self, output_path: Path, violations: Optional[List['Violation']] = None) -> None:
        """Export graph as JSON for visualization, highlighting violations."""
        with sqlite3.connect(self.db_path) as conn:
            # Get all symbols
            cursor = conn.execute("SELECT * FROM symbols")
            symbols = [
                {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'file': row[3],
                    'docstring': row[6]
                }
                for row in cursor
            ]

            # Get all relationships
            cursor = conn.execute("SELECT source_id, target_id, rel_type FROM relationships")
            relationships = [
                {'source': row[0], 'target': row[1], 'type': row[2]}
                for row in cursor
            ]

        # Annotate violations
        if violations:
            violation_set = {(v.source_name, v.target_name) for v in violations}
            for edge in relationships:
                # Need to find names for source and target to match violation_set
                # or match by names directly
                # It's better to get symbol names from graph
                s_name = next((s['name'] for s in symbols if s['id'] == edge['source']), "")
                t_name = next((s['name'] for s in symbols if s['id'] == edge['target']), "")
                if (s_name, t_name) in violation_set:
                    edge['is_violation'] = True
                    edge['violation_rule'] = next(v.constraint for v in violations if v.source_name == s_name and v.target_name == t_name)

        data = {
            'nodes': symbols,
            'edges': relationships
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"✓ Graph visualization data saved to {output_path}")
