"""Generate architectural reports from the knowledge graph."""

from pathlib import Path
import logging
from .graph import CodeGraph

logger = logging.getLogger(__name__)

class GraphReporter:
    """Analyze knowledge graph and generate human-readable reports."""

    def __init__(self, graph: CodeGraph):
        self.graph = graph

    def generate_report(self, output_path: Path) -> str:
        """Create a Markdown report with architectural insights."""
        stats = self.graph.get_statistics()
        god_nodes = self.graph.get_central_nodes(limit=5)
        surprising = self.graph.get_surprising_connections(limit=8)

        report = f"""# PCIL Intelligence Report

This report summarizes the architectural structure and "intelligence layer" discovered in the workspace.

## 📊 Overview
- **Total Symbols Indexed**: {stats['total_symbols']}
- **Relationships Found**: {stats['total_relationships']}
- **Graph Density**: {stats['total_relationships'] / max(stats['total_symbols'], 1):.2f} edges/node

## 👑 God Nodes
*Symbols with the highest connectivity. These are the core anchors of your architecture.*

"""
        for node in god_nodes:
            report += f"- **{node['name']}** ({node['type']}): {node['degree']} connections\n"
            report += f"  - *Location*: `{node['file_path']}`\n"
            if node['docstring']:
                report += f"  - *Summary*: {node['docstring'].split('.')[0]}...\n"
            report += "\n"

        report += """## 🔗 Surprising Connections
*Key relationships that cross between different modules or files.*

"""
        for conn in surprising:
            source_name = conn['source'].split('::')[1] if '::' in conn['source'] else conn['source']
            target_name = conn['target'].split('::')[1] if '::' in conn['target'] else conn['target']
            report += f"- `{source_name}` → `{target_name}` ({conn['type']})\n"
            report += f"  - {Path(conn['source_file']).name} to {Path(conn['target_file']).name}\n"

        report += """
## ❓ Suggested Questions
*The graph is uniquely positioned to answer these architectural questions.*

"""
        if god_nodes:
            core = god_nodes[0]['name']
            report += f"- How does the logic flow from `{core}` to its dependencies?\n"
            report += f"- What are the side effects of modifying the docstring of `{core}`?\n"
        
        report += "- Show me the shortest path between the main entry point and storage logic.\n"
        report += "- Which modules are the most isolated (lowest degree)?\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)

        logger.info(f"✓ Architectural report generated at {output_path}")
        return report
