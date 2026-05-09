# Contributing to Archon AI

Thanks for your interest! Here's how to get set up.

## Dev Setup

```bash
git clone https://github.com/srujanasru0521-create/archon.git
cd archon
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Project Layout

| Folder/File | What it's for |
|---|---|
| `archon/parsers/` | Language parsers — add new languages here |
| `archon/sentry.py` | Architectural constraint checking |
| `archon/impact.py` | Blast radius calculation |
| `archon/graph.py` | SQLite knowledge graph |
| `archon/cli.py` | All CLI commands |

## Adding a New Language Parser

1. Create `archon/parsers/your_language_parser.py`
2. Inherit from `BaseParser` in `archon/parsers/base.py`
3. Implement `parse_file()` and `analyze_workspace()`
4. Register your parser in `archon/rag.py`

## Commit Style

Use conventional commits:
- `feat: add TypeScript parser`
- `fix: blast radius skipping depth 0`
- `docs: update README with new commands`
