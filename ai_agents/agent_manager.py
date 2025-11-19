# ai_agents/agent_manager.py
from crew.crew_manager import create_agent
from ai_agents import sdk_tools
from logger import log

# create agents you'll use
AGENTS = {
    "ArchitectAgent": create_agent("ArchitectAgent", tools={
        "search_vector": sdk_tools.search_vector,
        "read_memory": sdk_tools.read_memory,
        "append_memory": sdk_tools.append_memory,
        "detect_intent": sdk_tools.detect_intent,
    }),
    "ImpactAgent": create_agent("ImpactAgent", tools={
        "search_vector": sdk_tools.search_vector, "read_memory": sdk_tools.read_memory, "append_memory": sdk_tools.append_memory
    }),
    "BlueprintAgent": create_agent("BlueprintAgent", tools={
        "search_vector": sdk_tools.search_vector, "read_memory": sdk_tools.read_memory, "append_memory": sdk_tools.append_memory
    }),
    "UnderstandingAgent": create_agent("UnderstandingAgent", tools={
        "search_vector": sdk_tools.search_vector, "read_memory": sdk_tools.read_memory
    }),
}

def run_agent(agent_key: str, query: str, topk: int = 6):
    agent = AGENTS.get(agent_key)
    if not agent:
        log.error("Unknown agent: " + agent_key)
        return "Unknown agent"
    # quick retrieval step
    ctx, docs = sdk_tools.search_vector(query, topk=topk)
    # include memory if needed
    mem = sdk_tools.read_memory()
    # we pass only retrieved context (to keep prompt compact); agents can call sdk_tools themselves if advanced
    out = agent.run(query, retrieved_context=ctx)
    return out  

if __name__ == "__main__":
    test_query = "Explain the impact of AI on modern software development."
    response = run_agent("ImpactAgent", test_query)
    print("Agent Response:", response)
