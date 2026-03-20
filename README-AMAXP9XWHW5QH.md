# 🧠 Agentic Architect AI — RAG + Gemini

An intelligent, multi-agent architecture assistant that can:
- Analyze microservices codebases
- Identify architecture patterns, flows, and dependencies
- Evaluate impact of changes
- Generate blueprints and technical documentation automatically

---

## 🚀 Features

- Multi-agent orchestration (Understanding, Impact, Blueprint, Doc Generation)
- RAG-based retrieval using ChromaDB
- Persistent chat history (SQLite)
- Markdown-based doc generation
- Modular architecture for extension

---

## 🧩 Folder structure (high level)

- `ai_agents/`: orchestrator and agent implementations (Architect, Understanding, Impact, Blueprint, DocGen)
- `crew/`: lightweight local agent wrapper (`crew_manager.py`)
- `tools/`: embeddings, vector-store, code analysis helpers
- `chroma_db/`: vector DB files
- `generated_docs/`: produced documentation

---

## ⚙️ Installation & setup

1) Clone and create a virtualenv

```bash
git clone <your_repo_url>
cd rag-agentic-poc
python -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Configuration

- Review `config.yaml` and adjust `app.persist_dir`, `app.metadata_dir`, and `app.db_path` if needed.
- Optionally set an LLM API key (example environment variable used in this repo):

```bash
export GEMINI_API_KEY="your_key_here"
```

Notes:
- If you plan to analyze a large codebase, build the vector index first (see "Rebuild vector index" below).

---

## ▶️ Run

- Streamlit UI (recommended):

```bash
streamlit run main.py
```

- Quick agent test (CLI):

```bash
python -c "from ai_agents.agent_manager import run_agent; print(run_agent('ImpactAgent', 'If we add a new auth middleware, what modules are impacted?'))"
```

---

## 🔁 Rebuild vector index

If you update or want to (re)index a repository for RAG retrieval, use the embedder utility:

```python
from tools.embedder import Embedder
Embedder.embed_codebase(repo_path='path/to/repo', persist_dir='chroma_db')
```

This writes vector index files into `chroma_db/` and metadata into `data/metadata/`.

---

## 📐 Architecture

See `docs/ARCHITECTURE.md` for a diagram and component descriptions.

High level:

- `main.py` / Streamlit: UI that sends queries to the `ArchitectAgent` orchestrator.
- `ai_agents/architect_agent.py`: intent detection, RAG retrieval, delegate to sub-agents, persist chat via `ai_agents.db.ChatDB`.
- Domain agents (`ai_agents/*_agent.py`) implement `analyze`/`generate` and are registered in `ai_agents/agent_manager.py` via the `crew` wrapper.
- `tools/` includes `embedder.py`, `code_analyzer.py`, and SDK helpers used for RAG and analysis.
