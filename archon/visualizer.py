"""Generate interactive HTML visualizations of the knowledge graph."""

import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PCIL Knowledge Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #0f172a; color: #f8fafc; overflow: hidden; }}
        #mynetwork {{ width: 100vw; height: 100vh; background-color: #0f172a; }}
        .controls {{ position: absolute; top: 20px; left: 20px; z-index: 10; background: rgba(30, 41, 59, 0.8); padding: 15px; border-radius: 8px; border: 1px solid #334155; backdrop-filter: blur(4px); }}
        h1 {{ margin: 0 0 10px 0; font-size: 18px; color: #38bdf8; }}
        .legend {{ display: flex; gap: 15px; font-size: 12px; margin-top: 10px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .search {{ margin-top: 10px; }}
        input {{ background: #1e293b; border: 1px solid #334155; color: white; padding: 5px; border-radius: 4px; width: 100%; }}
    </style>
</head>
<body>
    <div class="controls">
        <h1>PCIL Explorer</h1>
        <div class="legend">
            <div class="legend-item"><span class="dot" style="background: #38bdf8;"></span> Function</div>
            <div class="legend-item"><span class="dot" style="background: #a855f7;"></span> Class</div>
        </div>
        <div class="search">
            <input type="text" id="nodeSearch" placeholder="Search symbols..." onkeyup="searchNodes()">
        </div>
        <div id="status" style="font-size: 10px; margin-top: 10px; color: #94a3b8;">Loading nodes...</div>
    </div>
    <div id="mynetwork"></div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});

        // Track violated nodes for glowing effect
        var violatedNodes = new Set();
        edges.update(edges.get().map(edge => {{
            if (edge.is_violation) {{
                edge.color = {{ color: '#ef4444', highlight: '#f87171', hover: '#f87171' }};
                edge.width = 4;
                edge.title = "⚠️ VIOLATION: " + edge.violation_rule;
                edge.dashes = true;
                violatedNodes.add(edge.source);
                violatedNodes.add(edge.target);
            }}
            return edge;
        }}));

        // Add colors based on type and violations
        nodes.update(nodes.get().map(node => {{
            if (node.type === 'function') node.color = '#38bdf8';
            else if (node.type === 'class') node.color = '#a855f7';
            
            if (violatedNodes.has(node.id)) {{
                node.shadow = {{ color: '#ef4444', size: 20, x: 0, y: 0 }};
                node.borderWidth = 3;
                node.color = {{ border: '#ef4444', background: node.color }};
            }}
            
            node.label = node.name;
            node.title = node.docstring || node.id;
            return node;
        }}));

        var container = document.getElementById('mynetwork');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            nodes: {{
                shape: 'dot',
                size: 16,
                font: {{ color: '#f1f5f9', size: 12 }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 2,
                color: {{ color: '#475569', highlight: '#38bdf8', hover: '#38bdf8' }},
                arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
                smooth: {{ type: 'curvedCW', roundness: 0.2 }}
            }},
            physics: {{
                forceAtlas2Based: {{
                    gravitationalConstant: -26,
                    centralGravity: 0.005,
                    springLength: 230,
                    springConstant: 0.18
                }},
                maxVelocity: 146,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: {{ iterations: 150 }}
            }},
            interaction: {{ hover: true, tooltipDelay: 200 }}
        }};
        var network = new vis.Network(container, data, options);

        network.on("stabilizationIterationsDone", function () {{
            document.getElementById('status').innerText = nodes.length + ' symbols connected';
        }});

        function searchNodes() {{
            var input = document.getElementById('nodeSearch').value.toLowerCase();
            var allNodes = nodes.get();
            if (!input) {{
                nodes.update(allNodes.map(n => ({{ id: n.id, hidden: false }})));
                return;
            }}
            nodes.update(allNodes.map(n => ({{
                id: n.id,
                hidden: !n.name.toLowerCase().includes(input)
            }})));
        }}
    </script>
</body>
</html>
"""

class GraphVisualizer:
    """Generate interactive HTML visualizations."""

    def __init__(self, data_path: Path):
        self.data_path = data_path

    def generate_html(self, output_path: Path):
        """Build the HTML file using visualization data."""
        with open(self.data_path, 'r') as f:
            data = json.load(f)

        html_content = HTML_TEMPLATE.format(
            nodes_json=json.dumps(data['nodes']),
            edges_json=json.dumps(data['edges'])
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html_content)

        logger.info(f"✓ Interactive visualization generated at {output_path}")
