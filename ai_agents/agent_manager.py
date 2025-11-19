# ai_agents/agent_manager.py
from crew.crew_manager import create_agent
from ai_agents import sdk_tools
from logger import log

# Import concrete agent implementations so we can provide them as handlers
from ai_agents.impact_agent import ImpactAnalyzerAgent
from ai_agents.understanding_agent import UnderstandingAgent
from ai_agents.blueprint_agent import BlueprintGeneratorAgent
from ai_agents.architect_agent import run_agent_sync as architect_run_sync


# create agents you'll use (handlers delegate to existing implementations)
AGENTS = {
    "ArchitectAgent": create_agent("ArchitectAgent", tools={
        "search_vector": sdk_tools.search_vector,
        "read_memory": sdk_tools.read_memory,
        "append_memory": sdk_tools.append_memory,
        "detect_intent": sdk_tools.detect_intent,
    }, handler=architect_run_sync),
    "ImpactAgent": create_agent("ImpactAgent", tools={
        "search_vector": sdk_tools.search_vector,
    }, handler=ImpactAnalyzerAgent()),
    "BlueprintAgent": create_agent("BlueprintAgent", tools={
        "search_vector": sdk_tools.search_vector,
    }, handler=BlueprintGeneratorAgent()),
    "UnderstandingAgent": create_agent("UnderstandingAgent", tools={
        "search_vector": sdk_tools.search_vector,
    }, handler=UnderstandingAgent()),
}


def run_agent(agent_key: str, query: str, topk: int = 6):
    agent = AGENTS.get(agent_key)
    if not agent:
        log.error("Unknown agent: %s", agent_key)
        return "Unknown agent"

    # quick retrieval step (sdk_tools.search_vector returns a dict)
    res = sdk_tools.search_vector(query, top_k=topk)
    docs = res.get("documents", [])
    metadatas = res.get("metadatas", [])

    # build a compact context string
    context_pieces = []
    if isinstance(docs, list):
        for i, doc in enumerate(docs[:topk]):
            src = None
            try:
                src = metadatas[i].get("source") if i < len(metadatas) else None
            except Exception:
                src = None
            context_pieces.append(f"Source: {src}\n{doc}")
    ctx = "\n\n---\n\n".join(context_pieces) if context_pieces else ""

    out = agent.run(query, retrieved_context=ctx)
    return out


if __name__ == "__main__":
    test_query = "Explain the impact of AI on modern software development."
    response = run_agent("ImpactAgent", test_query)
    print("Agent Response:", response)
