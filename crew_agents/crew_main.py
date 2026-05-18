# crew_agents/crew_main.py
import os
from dotenv import load_dotenv
from crew_agents.crew_router import route_to_agent
from ai_agents.sdk_tools import search_vector, detect_intent

load_dotenv()

def run_crew_agent(user_input, persist_dir="chroma_db"):
    # Step 1: Detect intent
    intent = detect_intent(user_input)
    # Step 2: Retrieve RAG context
    context, _ = search_vector(user_input, top_k=5, persist_dir=persist_dir)
    # Step 3: Route to Crew agent
    result = route_to_agent(user_input, context, intent)
    return {"agent": intent, "response": result}

if __name__ == "__main__":
    user_input = input("Enter your query: ")
    print(run_crew_agent(user_input))
