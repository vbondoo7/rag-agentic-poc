## Quick context

This repo implements an agentic, RAG-enabled architecture assistant (Streamlit UI + multi-agent orchestration). The main orchestration entry point is `ai_agents/architect_agent.py` (intent detection -> RAG retrieval -> delegate to sub-agents -> persist chat). The Streamlit UI at `main.py` calls `ai_agents.architect_agent.run_agent_sync()` and expects the agent to NOT directly write to the DB — persistence is centralized in `ai_agents.architect_agent` via `ai_agents.db.ChatDB`.

## High-level architecture (what to know immediately)
- Agents live in `ai_agents/` (Understanding, Impact, Blueprint, DocGenerator, Requirements, etc.). Each agent exposes a simple method (e.g., `analyze`, `generate`) that accepts `user_input` and `context`.
- `ai_agents/agent_manager.py` registers agents and wires tool functions (from `ai_agents/sdk_tools`) into agent instances. If you add an agent, register it here and provide required tools.
- Retrieval & embeddings: `tools/embedder.py` and `ai_agents/sdk_tools.search_vector` perform RAG lookup into the Chroma DB at `chroma_db/` (persist dir configured in `config.yaml`).
- Code analysis utilities are in `tools/code_analyzer.py` (tree-sitter if available, else regex heuristics) and write per-file metadata to `data/metadata/`.
- Chat persistence: `ai_agents/db.py` / `ai_agents.db.ChatDB` — chat summary fields are managed by orchestration (see `architect_agent.py`).

## Important developer workflows
- Run the GUI (Streamlit): use the project virtualenv and then run `streamlit run main.py` from repo root. `main.py` will read `config.yaml` for `app.persist_dir`, `app.metadata_dir`, and `app.db_path`.
- Rebuild vector index: either click "Rebuild Vector Index (force)" in the Streamlit sidebar or call `Embedder.embed_codebase(repo_path, persist_dir)` (see `tools/embedder.py`). The vector DB files are stored in `chroma_db/`.
- Indexing/analysis output: `tools/code_analyzer.analyze_folder()` writes JSON metadata into `data/metadata/` — useful for agent retrieval and documentation generation.

## Conventions agents must follow (concrete)
- Agents should NOT write to the chats DB directly. Return results to the orchestrator. `ai_agents/architect_agent.run_agent_sync()` handles DB persistence via `ChatDB.add_chat` / `add_message` / `update_chat_response`.
- Intent labels used by router: `impact`, `blueprint`, `documentation`, `understanding` (fallback to `understanding`/generic). See `ai_agents/architect_agent.py` routing.
- RAG call shape: `search_vector(query, top_k=5, persist_dir=...)` returns a dict containing `documents` and `metadatas`. `architect_agent` joins docs into a single `context` string truncated to ~60000 chars.
- Tooling pattern: add helper functions to `ai_agents/sdk_tools.py` and then pass them into `agent_manager.create_agent(...)` mapping. Agents expect tools like `search_vector`, `read_memory`, `append_memory`, `detect_intent` to be available when run.

## Files and locations to reference when coding
- Orchestration & routing: `ai_agents/architect_agent.py`
- Agent registration: `ai_agents/agent_manager.py` and `crew/crew_manager.py` (factory helpers)
- SDK tools: `ai_agents/sdk_tools.py` (search_vector, read_memory, append_memory, detect_intent)
- Streamlit UI & config usage: `main.py`, `config.yaml`
- Embedding + vector store: `tools/embedder.py`, `chroma_db/`
- Code analysis helpers: `tools/code_analyzer.py` -> `data/metadata/`
- DB schema & helpers: `db/` and `ai_agents/db.py` (chat storage)

## Small examples to follow
- Registering an agent: add an entry to `AGENTS` in `ai_agents/agent_manager.py` and supply tools from `ai_agents/sdk_tools` (see existing `ArchitectAgent` entry).
- Returning structured agent outputs: agents should return either a simple string or a dict with `{"response": ..., "agent": "Name"}`; `architect_agent` normalizes both shapes.

## Quick dos & don'ts (project-specific)
- Do: Use `ai_agents/sdk_tools.search_vector` for retrieval so results include consistent metadata (source) used in doc generation.
- Do: Keep per-file metadata generation in `tools/code_analyzer.py` (it is used by embedder/metadata workflows). Use tree-sitter when available; fall back to heuristics.
- Don't: Modify DB directly from inside agents. Let `architect_agent` persist chat summaries and messages.

## Need-to-ask / unknowns for iteration
- Do you want agents to be allowed to write incremental memory entries? Current flow uses `sdk_tools.append_memory` but persistence location/format isn't fully documented in repo; confirm expected memory store.
- Any preferred intent label additions beyond the 4 above?

If this looks good I will commit this file. Tell me if you want different wording, additional examples, or extra workflow commands to be included (tests, lint, or CI steps).
