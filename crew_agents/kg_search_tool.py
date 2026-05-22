"""
CrewAI-compatible Knowledge Graph search tool.
"""
from rdflib import Graph
import os

def kg_search(input, context=None):
    # Load the KG (assume Turtle format, built by kg_builder.py)
    kg_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.ttl')
    g = Graph()
    g.parse(kg_path, format="turtle")
    query = input if isinstance(input, str) else input.get('query', '')
    # Simple SPARQL: search for files/entities containing the keyword
    sparql = f'''
    SELECT ?file ?dir WHERE {{
      ?file <http://example.org/kg/inDirectory> ?dir .
      FILTER(CONTAINS(LCASE(STR(?file)), LCASE("{query}")))
    }} LIMIT 10
    '''
    results = g.query(sparql)
    context_str = "\n".join([f"File: {str(row.file).split('/')[-1]}, Dir: {row.dir}" for row in results])
    return context_str or "No relevant facts found."
