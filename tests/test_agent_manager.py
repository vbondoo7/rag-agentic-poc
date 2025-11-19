from ai_agents import agent_manager
from crew.crew_manager import create_agent


def test_run_agent_with_overridden_handlers(tmp_path, monkeypatch):
    # monkeypatch search_vector to a predictable result
    monkeypatch.setattr(agent_manager, 'sdk_tools', agent_manager.sdk_tools)
    def fake_search(q, top_k=6):
        return {"documents": ["doc1"], "metadatas": [{"source": "s1"}]}
    monkeypatch.setattr(agent_manager.sdk_tools, 'search_vector', fake_search)

    # override AGENTS to avoid LLM calls
    backup = dict(agent_manager.AGENTS)
    agent_manager.AGENTS['UnderstandingAgent'] = create_agent('UnderstandingAgent', handler=lambda q,c: 'understood')
    agent_manager.AGENTS['ImpactAgent'] = create_agent('ImpactAgent', handler=lambda q,c: 'impacted')

    try:
        out1 = agent_manager.run_agent('UnderstandingAgent', 'what is this?')
        assert out1 == 'understood'
        out2 = agent_manager.run_agent('ImpactAgent', 'what is impacted?')
        assert out2 == 'impacted'
    finally:
        agent_manager.AGENTS.clear()
        agent_manager.AGENTS.update(backup)
