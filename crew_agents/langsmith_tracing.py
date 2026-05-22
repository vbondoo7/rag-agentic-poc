"""
LangSmith tracing utility for CrewAI system.
"""
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from langsmith import Client
    LANGSMITH_ENABLED = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
    client = Client(api_key=LANGSMITH_API_KEY, project=LANGSMITH_PROJECT) if LANGSMITH_ENABLED else None
except ImportError:
    LANGSMITH_ENABLED = False
    client = None

def log_trace(user_input, agent_name, agent_response):
    if not LANGSMITH_ENABLED or not client:
        return
    try:
        client.create_trace(
            input=user_input,
            output=agent_response,
            agent=agent_name
        )
    except Exception as e:
        print(f"LangSmith trace error: {e}")
