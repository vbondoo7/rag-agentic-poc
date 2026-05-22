"""
Knowledge Graph (KG) builder for codebase analysis.
Extracts file/folder structure and basic code entities as RDF triples using rdflib.
"""
import os
from rdflib import Graph, Namespace, Literal, RDF

KG_NS = Namespace("http://example.org/kg/")

def build_knowledge_graph(base_dir, exclude_dirs=None):
    exclude_dirs = set(exclude_dirs or [])
    g = Graph()
    g.bind("kg", KG_NS)
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_dir)
            # Add file as an entity
            g.add((KG_NS[rel_path], RDF.type, KG_NS.File))
            g.add((KG_NS[rel_path], KG_NS.inDirectory, Literal(root)))
            # Optionally: parse file for classes/functions and add more triples
    return g

def save_kg(graph, path):
    graph.serialize(destination=path, format="turtle")

# Example usage:
# g = build_knowledge_graph('sample_codebase/microservices-demo', exclude_dirs=[...])
# save_kg(g, 'crew_agents/knowledge_graph.ttl')
