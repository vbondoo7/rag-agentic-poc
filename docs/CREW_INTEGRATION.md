Crew-like agent wrapper

This project includes a small, local "crew" wrapper `crew/crew_manager.py` that provides a simple Agent abstraction. Agents may either:

- Delegate to an existing Python handler (recommended) — e.g. the existing `ai_agents/impact_agent.py` provides `ImpactAnalyzerAgent.analyze()` and is wrapped by the crew agent registry in `ai_agents/agent_manager.py`.
- Or fall back to using the configured generative model prompt templates if a handler is not provided.

How to run a quick agent (python):

```bash
python -c "from ai_agents.agent_manager import run_agent; print(run_agent('ImpactAgent', 'What modules are impacted by changing the auth flow?'))"
```

Notes:
- Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in your environment to enable LLM calls.
- The crew wrapper gracefully handles missing `google.generativeai` by requiring a handler; otherwise LLM calls will report as unavailable.
