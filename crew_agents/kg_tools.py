"""
CrewAI-compatible tool for knowledge graph retrieval.
"""
from crew_agents.knowledge_graph import get_kg

def kg_search(input, context=None):
    query = input if isinstance(input, str) else input.get('query', '')
    kg = get_kg()
    results = kg.search(query)
    # Format results as context string
    context_str = "\n".join([f"{s.split('/')[-1]} {p.split('/')[-1]} {o}" for s, p, o in results])
    return context_str or "No relevant facts found."
