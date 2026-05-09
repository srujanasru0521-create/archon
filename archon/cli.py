"""Command-line interface for Archon AI."""


from pathlib import Path
from typing import Optional
import typer
import logging
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel

from .rag import CodeRAG, create_rag_prompt
from .reporter import GraphReporter
from .visualizer import GraphVisualizer
from .impact import BlastRadiusCalculator

# Setup logging and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

app = typer.Typer(help="Archon AI - The Self-Governing Knowledge Graph")


@app.command()
def init(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    )
):
    """Initialize a new Archon context in the workspace."""
    ws = workspace or Path.cwd()
    context_dir = ws / ".ai_context"
    
    if context_dir.exists():
        console.print(f"✨ Archon already initialized in {ws}", style="yellow")
    else:
        context_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"🚀 Initialized Archon context in {context_dir}", style="green")
    
    # Initialize components
    try:
        rag = CodeRAG(workspace_root=ws)
        console.print("✅ Components initialized", style="green")
    except Exception as e:
        console.print(f"❌ Error during initialization: {e}", style="red")


@app.command()
def index(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    )
):
    """Index all Python files in workspace and save to .ai_context."""
    ws = workspace or Path.cwd()
    
    if not ws.exists():
        console.print(f"❌ Workspace not found: {ws}", style="red")
        raise typer.Exit(1)
    
    console.print(f"📚 Indexing workspace: {ws}")
    
    try:
        rag = CodeRAG(workspace_root=ws)
        rag.index_workspace()
        console.print(f"✅ Success! Data persisted to {ws}/.ai_context", style="green")
    
    except Exception as e:
        console.print(f"❌ Error during indexing: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def explore(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    )
):
    """Generate architectural report and interactive visualization."""
    ws = workspace or Path.cwd()
    try:
        rag = CodeRAG(workspace_root=ws)
        if not rag.vector_path.exists():
            console.print("📚 No index found. Building intelligence layer...")
            rag.index_workspace()
        
        console.print("🧐 Analyzing architecture...")
        
        # 1. Generate Report
        report_path = rag.context_dir / "GRAPH_REPORT.md"
        reporter = GraphReporter(rag.graph)
        reporter.generate_report(report_path)
        console.print(f"📄 Report generated: {report_path}", style="green")

        # Run Sentry for visualization
        from .sentry import ConstraintChecker
        sentry = ConstraintChecker(ws, rag.graph)
        violations = sentry.check_constraints()
        if violations:
            console.print(f"⚠️  Found {len(violations)} architectural violations. Visualizing them in red.", style="red bold")
        
        # 2. Generate Visualization
        viz_data_path = rag.context_dir / "viz_data.json"
        rag.graph.save_visualization(viz_data_path, violations=violations)
        
        viz_html_path = rag.context_dir / "graph.html"
        visualizer = GraphVisualizer(viz_data_path)
        visualizer.generate_html(viz_html_path)
        console.print(f"🌐 Visualization generated: {viz_html_path}", style="green")
        
        console.print("\n✨ Exploration complete. Open the HTML file to view the graph!", style="cyan")

    except Exception as e:
        console.print(f"❌ Error during exploration: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def impact(
    target_id: str = typer.Argument(..., help="Symbol ID to analyze"),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    )
):
    """Calculate the blast radius of modifying a symbol."""
    ws = workspace or Path.cwd()
    try:
        rag = CodeRAG(workspace_root=ws)
        if not rag.graph_path.exists():
            console.print("📚 No index found. Building intelligence layer...")
            rag.index_workspace()

        calculator = BlastRadiusCalculator(rag.graph)
        console.print(f"💥 Calculating blast radius for {target_id}...")
        
        affected = calculator.calculate_impact(target_id)
        
        if not affected:
            console.print("✅ No downstream dependencies found. Safe to modify.", style="green")
            return
            
        table = Table(title=f"Blast Radius", show_header=True)
        table.add_column("Depth", style="cyan")
        table.add_column("Component", style="magenta")
        table.add_column("File", style="green")
        table.add_column("Directly Impacted By", style="yellow")
        
        for k, v in sorted(affected.items(), key=lambda item: item[1]['depth']):
            impactors = [i.split('::')[1] if '::' in i else i for i in v['impacted_by']]
            table.add_row(
                str(v['depth']),
                v['name'],
                str(Path(v['file_path']).name),
                ", ".join(impactors)
            )
            
        console.print(table)
        console.print(f"\n⚠️ Total components impacted: {len(affected)}", style="red bold")

    except Exception as e:
        console.print(f"❌ Error during impact analysis: {e}", style="red")
        raise typer.Exit(1)

@app.command()
def install_antigravity(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    )
):
    """Install PCIL rules and workflows for Google Antigravity."""
    ws = workspace or Path.cwd()
    agent_dir = ws / ".agent"
    
    try:
        # 1. Rules
        rules_dir = agent_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        rules_content = """# PCIL Rules
Knowledge graph exists for this codebase.

- Always read `.ai_context/GRAPH_REPORT.md` before answering architecture questions.
- If a user asks "how does X work", use `archon query` to find the most relevant symbols.
- Use the Knowledge Graph to navigate by structure rather than keyword searching.
"""
        with open(rules_dir / "archon.md", "w") as f:
            f.write(rules_content)
            
        # 2. Workflows
        workflows_dir = agent_dir / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflows_content = """# PCIL Workflows
Register /archon as a slash command.

- `/archon query <question>`: Run semantic search.
- `/archon explore`: Regenerate the architectural report and graph.
- `/archon info`: Show index statistics.
"""
        with open(workflows_dir / "archon.md", "w") as f:
            f.write(workflows_content)
            
        console.print(f"✅ Antigravity integration installed in {agent_dir}", style="green")
        console.print("💡 Refresh your workspace to see the new rules and slash command.", style="blue")

    except Exception as e:
        console.print(f"❌ Error installing integration: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def query(
    question: str = typer.Argument(..., help="Natural language query"),
    index_file: Optional[Path] = typer.Option(
        None,
        "--index",
        "-i",
        help="Path to index file"
    ),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    ),
    results: int = typer.Option(
        5,
        "--results",
        "-k",
        help="Number of results to return"
    )
):
    """Query code with natural language."""
    try:
        rag = CodeRAG(workspace_root=workspace or Path.cwd())
        
        # Load index if provided (overrides default .ai_context)
        if index_file and index_file.exists():
            console.print(f"📂 Loading override index: {index_file}")
            rag.load_index(index_file)
        elif not rag.vector_path.exists():
            console.print("📚 No index found. Building index first...")
            rag.index_workspace()
        
        # Retrieve results
        console.print(f"🔍 Searching: {question}\n")
        retrieved = rag.retrieve(question, k=results)
        
        if not retrieved:
            console.print("❌ No results found", style="yellow")
            return
        
        # Display results
        table = Table(title="Search Results", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("File", style="green")
        table.add_column("Similarity", style="yellow")
        
        for result in retrieved:
            table.add_row(
                result.name,
                result.signature.split('(')[0].replace('def ', '').replace('class ', ''),
                str(result.file_path),
                f"{result.similarity:.1%}"
            )
        
        console.print(table)
        
        # Show details for top result
        if retrieved:
            top = retrieved[0]
            console.print("\n")
            console.print(Panel(
                top.docstring or "No documentation",
                title=f"📖 {top.name} Documentation",
                border_style="blue"
            ))
            console.print(f"\n📍 Location: {top.file_path}")
    
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def prompt(
    question: str = typer.Argument(..., help="Question for LLM"),
    index_file: Optional[Path] = typer.Option(
        None,
        "--index",
        "-i",
        help="Path to index file"
    ),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    ),
    results: int = typer.Option(
        3,
        "--results",
        "-k",
        help="Number of context results"
    )
):
    """Generate RAG-augmented prompt for LLM."""
    try:
        rag = CodeRAG(workspace_root=workspace or Path.cwd())
        
        # Load or build index
        if index_file and index_file.exists():
            rag.load_index(index_file)
        elif not rag.vector_path.exists():
            console.print("📚 No index found. Building index...")
            rag.index_workspace()
        
        # Generate prompt
        console.print(f"🤖 Generating RAG prompt for: {question}\n")
        retrieved = rag.retrieve(question, k=results)
        generated_prompt = create_rag_prompt(question, retrieved)
        
        # Display with syntax highlighting
        syntax = Syntax(
            generated_prompt,
            "markdown",
            theme="monokai",
            line_numbers=False
        )
        console.print(syntax)
    
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def watch(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory to watch"
    )
):
    """Watch repository for changes and automatically re-index."""
    ws = workspace or Path.cwd()
    
    if not ws.exists():
        console.print(f"❌ Workspace not found: {ws}", style="red")
        raise typer.Exit(1)
        
    console.print(f"👀 Starting file watcher in {ws}", style="cyan")
    try:
        from .sync import FileWatcher
        # We need an initialized RAG with the full workspace already indexed (or it'll index on the fly when we run it initially)
        rag = CodeRAG(workspace_root=ws)
        console.print("📚 Checking initial index...", style="cyan")
        rag.index_workspace()
        
        watcher = FileWatcher(rag)
        watcher.start(ws)
    except ModuleNotFoundError:
        console.print("❌ Missing dependency 'watchdog'. Install with: pip install watchdog", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error starting watcher: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def info(
    index_file: Optional[Path] = typer.Option(
        None,
        "--index",
        "-i",
        help="Path to index file"
    ),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root directory"
    )
):
    """Display index information."""
    try:
        rag = CodeRAG(workspace_root=workspace or Path.cwd())
        
        if index_file and index_file.exists():
            rag.load_index(index_file)
            source = f"from {index_file}"
        else:
            console.print("📚 Analyzing workspace...")
            rag.index_workspace()
            source = "from workspace"
        
        # Display info
        console.print(Panel(
            f"""
[bold]Index Information[/bold]

Total Symbols: {len(rag.vector_store.index)}
Source: {source}
Embedding Dimension: {rag.vector_store.embedding_dim}

Symbol Types:
  - Functions
  - Classes
  - Methods
""",
            title="📊 Archon AI Index"

        ))
    
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version",
        is_flag=True
    )
):
    """Archon AI - The Self-Governing Architectural Knowledge Graph"""

    if version:
        from . import __version__
        console.print(f"Archon AI v{__version__}")

        raise typer.Exit()


if __name__ == "__main__":
    app()
