"""
Knowledge Graph module using rdflib for RAG-Architect CrewAI.
"""
from rdflib import Graph, Namespace, Literal, RDF, URIRef
import os

KG_PATH = os.path.join(os.path.dirname(__file__), "knowledge_graph.ttl")

class KnowledgeGraph:
    def __init__(self, path=KG_PATH):
        self.g = Graph()
        if os.path.exists(path):
            self.g.parse(path, format="turtle")
        self.ns = Namespace("http://example.org/kg/")

    def add_fact(self, subj, pred, obj):
        self.g.add((self.ns[subj], self.ns[pred], Literal(obj)))

    def save(self, path=KG_PATH):
        self.g.serialize(destination=path, format="turtle")

    def query(self, sparql_query):
        return self.g.query(sparql_query)

    def search(self, keyword, limit=5):
        # Simple keyword search in triples
        results = []
        for s, p, o in self.g:
            if keyword.lower() in str(s).lower() or keyword.lower() in str(p).lower() or keyword.lower() in str(o).lower():
                results.append((s, p, o))
            if len(results) >= limit:
                break
        return results

def get_kg():
    return KnowledgeGraph()
