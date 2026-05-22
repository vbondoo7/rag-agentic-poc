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
- `sample_codebase/`: example code used for demos and indexing

---

## ⚙️ Recommended local setup (macOS/Linux)

This project lives in a cloud-backed folder (OneDrive) in this repo, which can cause slow filesystem operations for Python package metadata. To avoid issues, create and use a Python virtual environment outside the synced folder.

1) Create a venv outside the repo (recommended location `~/.venvs`):

```bash
python3 -m venv ~/.venvs/rag-agentic-poc
source ~/.venvs/rag-agentic-poc/bin/activate
cd /path/to/rag-agentic-poc   # your repo working copy
```

2) Install dependencies. The full `requirements.txt` includes optional native packages that may need extra system libraries (e.g. `pi-heif` for `unstructured[local-inference]`). For a fast first run install a filtered set that skips heavy optional native dependencies:

```bash
# quick (safe) install - excludes optional 'unstructured[local-inference]' heavy deps
pip install -r /path/to/rag-agentic-poc/requirements.txt --no-deps
pip install streamlit nest_asyncio pandas python-dotenv google-generativeai google-genai chromadb langchain-chroma langchain_community langchain_text_splitters sentence-transformers pydantic tqdm tree-sitter tree-sitter-languages PyYAML python-json-logger tiktoken
```

If you want the full feature set (file loaders with local inference), install system packages first (libheif, libjpeg, etc.) and then run:

```bash
pip install -r requirements.txt
```

(If pip fails building `pi-heif` / `pillow-heif`, follow installation instructions in https://pillow-heif.readthedocs.io.)

3) Optional: set an LLM API key (Gemini/Google). If you want the agents to call the LLM, set:

```bash
export GEMINI_API_KEY="your_key_here"
# or export GOOGLE_API_KEY="your_key_here"
```

Without this key the app will still run and return retrieved context as a safe fallback instead of making LLM calls.

---

## ▶️ Rebuild the vector index (RAG)

Before using retrieval you should build or refresh the vector index for the codebase you want to query.

```bash
source ~/.venvs/rag-agentic-poc/bin/activate
python - <<'PY'
from tools.embedder import Embedder
Embedder(persist_dir='chroma_db').embed_codebase('sample_codebase/microservices-demo')
PY
```

This writes vectors into `chroma_db/` and metadata into `data/metadata/`.

---

## ▶️ Run (Streamlit UI)

Start the UI from the venv (recommended):

```bash
source ~/.venvs/rag-agentic-poc/bin/activate
streamlit run main.py
```

Open http://localhost:8501 in your browser.

Quick CLI test (lightweight, returns fallback if no LLM key):

```bash
~/.venvs/rag-agentic-poc/bin/python -c "from ai_agents.agent_manager import run_agent; print(run_agent('ImpactAgent', 'If we add a new auth middleware, what modules are impacted?'))"
```

---

## Notes & troubleshooting

- If imports fail or you see timeouts when launching Python under a repo-backed `.venv` on OneDrive, recreate the venv outside the synced folder as above.
- If `pi-heif` fails to build, install system dependencies for `pillow-heif` (macOS `brew install libheif libde265` or follow pillow-heif docs) and re-run pip.
- The app logs warnings when `GEMINI_API_KEY` is not set — this is expected if you only want to test retrieval.

---

## Development & testing tips

- Add new agents under `ai_agents/` and register them in `ai_agents/agent_manager.py`.
- Use `tools/embedder.Embedder.embed_codebase()` when you change the codebase and need updated vectors.
- Chat persistence is handled by `ai_agents/db.py` (do not write to DB directly from agents).

---

## Architecture

See `docs/ARCHITECTURE.md` for diagrams and component descriptions.