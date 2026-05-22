"""
YAML loader for CrewAI agents and tasks.
"""
import yaml
import os

def load_yaml(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_agents():
    return load_yaml('agents.yaml')

def load_tasks():
    return load_yaml('tasks.yaml')
