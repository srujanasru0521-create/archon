# Archon AI 🛡️
### The Self-Governing Architectural Knowledge Graph

> **Archon AI** is an open-source developer tool that maps your entire codebase into a persistent Knowledge Graph, enforces your architectural rules automatically, and simulates the exact "blast radius" of any code change — all running locally, without sending code to any cloud.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)]()

---

## ✨ What Makes Archon Different

Most AI coding tools (Cursor, Copilot, etc.) forget your codebase on every session. Archon builds a **persistent local brain** for your project. But we went further:

| Feature | What it does |
|---|---|
| 🛡️ **Architectural Sentry** | Define rules in `archon.yaml`. Archon catches violations automatically on every index. |
| 💥 **Blast Radius Engine** | Know exactly which 60+ components will break before you touch a single file. |
| 🌐 **Lava-Red Visualizer** | Interactive 3D graph of your codebase — violations glow red so you can see your technical debt. |
| 🔍 **Semantic Search** | Search code by meaning, not keywords. `archon query "handle payment"` finds `process_cart_total()`. |
| 📡 **Model-Agnostic** | Works with any LLM. The intelligence lives in `.ai_context/`, not in the cloud. |
| 🌍 **Multi-Language Ready** | `BaseParser` interface scaffolded for TypeScript, Go, Rust — Python fully supported today. |

---

## 🚀 Quick Start

### Install

```bash
git clone https://github.com/srujanasru0521-create/archon.git
cd archon
pip install -e .
```

### Use on any project

```bash
# Go to any Python project
cd /path/to/your/project

# (Optional) Define your architectural rules
touch archon.yaml

# Step 1: Map the codebase
archon index

# Step 2: See violations in the interactive graph
archon explore
open .ai_context/graph.html

# Step 3: Simulate blast radius before touching a core file
archon impact MyImportantClass
```

---

## ⚙️ The `archon.yaml` Rules File

Drop this file in the root of any project to activate the Sentry Engine:

```yaml
layers:
  - name: CLI
    path: myapp/cli.py

  - name: API
    path: myapp/api/

  - name: Database
    path: myapp/models.py

constraints:
  - "CLI !-> Database"   # CLI must NEVER directly touch the Database
  - "API !-> CLI"        # API layer must not call CLI code
```

When you run `archon index`, the Sentry reads these rules and flags any violation in the terminal and renders it as a glowing red edge on the graph.

---

## 🖥️ All Commands

```bash
archon index              # Parse workspace, build Knowledge Graph + vector index
archon explore            # Generate GRAPH_REPORT.md + interactive graph.html
archon impact <name>      # Calculate blast radius of modifying a function/class
archon query "<text>"     # Semantic search by meaning
archon watch              # Auto re-index on every file save
archon info               # Show index statistics
```

---

## 🏗️ Architecture

```
Your Codebase
     │
     ▼
┌─────────────────────┐
│   Python Parser      │  ← Extracts functions, classes, imports via AST
│   (BaseParser)       │  ← Multi-language ready (TS/Go/Rust pluggable)
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌─────────┐  ┌──────────┐
│ SQLite  │  │ LanceDB  │
│ Graph   │  │ Vectors  │
│ (graph  │  │(index    │
│ .db)    │  │.json)    │
└────┬────┘  └────┬─────┘
     │             │
     ▼             ▼
┌──────────┐  ┌──────────┐
│ Sentry   │  │ RAG      │
│ Engine   │  │ Search   │
│(archon   │  │(semantic │
│.yaml)    │  │query)    │
└────┬─────┘  └──────────┘
     │
     ▼
┌──────────────────────┐
│  Blast Radius Engine  │  ← Recursive DFS on graph.db
│  Lava-Red Visualizer  │  ← vis.js interactive HTML
└──────────────────────┘
```

---

## 📦 Tech Stack

| Component | Technology |
|---|---|
| Parser | Python `ast` + `tree-sitter` (scaffolded) |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2, runs locally) |
| Vector DB | `LanceDB` / in-memory JSON |
| Knowledge Graph | SQLite |
| CLI | `Typer` + `Rich` |
| API | `FastAPI` |
| Visualization | `vis.js` (self-contained HTML) |

---

## 📁 Project Structure

```
archon/
├── archon/
│   ├── parsers/
│   │   ├── base.py            ← BaseParser interface (multi-lang contract)
│   │   └── python_parser.py   ← Python AST parser
│   ├── config.py              ← archon.yaml reader (Pydantic)
│   ├── sentry.py              ← 🛡️ Architectural Constraint Checker
│   ├── impact.py              ← 💥 Blast Radius Engine (recursive DFS)
│   ├── rag.py                 ← Orchestrator (glues all components)
│   ├── graph.py               ← SQLite Knowledge Graph
│   ├── embeddings.py          ← Embedding generation (local AI model)
│   ├── vector_store.py        ← Vector search engine
│   ├── visualizer.py          ← Interactive HTML graph generator
│   ├── reporter.py            ← Markdown report generator
│   ├── sync.py                ← File watcher (auto re-index)
│   └── cli.py                 ← Terminal commands (Typer)
├── tests/                     ← pytest test suite
├── examples/                  ← Usage examples
├── archon.yaml                ← Sample governance config
├── setup.py
└── requirements.txt
```

---

## 🤝 Contributing

Pull requests welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for the dev setup guide.

---

## 📝 License

MIT — see [LICENSE](./LICENSE)
