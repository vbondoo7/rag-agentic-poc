# CrewAI Integration for RAG-Architect

This folder contains a modular CrewAI-based agent orchestration setup for the RAG-Architect project. It does not modify or replace your existing agents, but provides a parallel, fully CrewAI-native implementation.

## Structure
- `crew_config.py`: Defines all CrewAI agents, tools, and the crew wiring. Provides a single entrypoint (`run_crew_agent`).
- `tools.py`: CrewAI-compatible wrappers for your existing SDK tools.
- `__init__.py`: Package marker.

## Usage
- Import and call `run_crew_agent(user_input, persist_dir)` from your Streamlit UI or any script.
- All agent routing, tool usage, and memory is handled via CrewAI.

## Requirements
- Install CrewAI: `pip install crewai`
- Your `.env` and vector DB setup should remain unchanged.

## Extending
- Add new agents or tools in `crew_config.py` and `tools.py` as needed.
- You can run both the legacy and CrewAI flows side-by-side for comparison or migration.
