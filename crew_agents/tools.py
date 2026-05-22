"""
CrewAI-compatible tool wrappers for RAG-Architect.
Wraps existing SDK tools for use in CrewAI agents.
"""
from ai_agents.sdk_tools import search_vector as _search_vector, detect_intent as _detect_intent, read_memory as _read_memory, append_memory as _append_memory

def search_vector(input, context=None):
    query = input if isinstance(input, str) else input.get('query', '')
    persist_dir = context.get('persist_dir', 'chroma_db') if context else 'chroma_db'
    _, docs_dict = _search_vector(query, persist_dir=persist_dir)
    return docs_dict

def detect_intent(input, context=None):
    query = input if isinstance(input, str) else input.get('query', '')
    return _detect_intent(query)

def read_memory(input=None, context=None):
    return _read_memory()

def append_memory(input, context=None):
    return _append_memory(input)
