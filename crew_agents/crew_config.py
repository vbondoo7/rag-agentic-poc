"""
CrewAI-based agent orchestration config for RAG-Architect.
Defines all agents, tools, and crew wiring in a modular, extensible way.
"""
from crewai import Crew, Agent, Task
from crew_agents.tools import (
    search_vector,
    detect_intent,
    read_memory,
    append_memory
)

# Define agents (roles)
impact_agent = Agent(
    name="ImpactAgent",
    description="Analyzes the impact of code changes or requirements.",
    tools=[search_vector, read_memory, append_memory],
)

blueprint_agent = Agent(
    name="BlueprintAgent",
    description="Generates architecture blueprints and diagrams.",
    tools=[search_vector, read_memory, append_memory],
)

doc_agent = Agent(
    name="DocGeneratorAgent",
    description="Generates and summarizes documentation.",
    tools=[search_vector, read_memory, append_memory],
)

understanding_agent = Agent(
    name="UnderstandingAgent",
    description="Explains code and answers understanding questions.",
    tools=[search_vector, read_memory],
)

requirements_agent = Agent(
    name="RequirementsAgent",
    description="Extracts and clarifies requirements from user input.",
    tools=[search_vector, read_memory, append_memory],
)

# Crew wiring (define the crew and routing logic)
crew = Crew(
    agents=[impact_agent, blueprint_agent, doc_agent, understanding_agent, requirements_agent],
    router=detect_intent,  # Use intent detection to route tasks
)

def run_crew_agent(user_input, persist_dir="chroma_db"):
    """Entrypoint for CrewAI-based agent orchestration."""
    # Create a task for the crew
    task = Task(
        input=user_input,
        context={"persist_dir": persist_dir}
    )
    # Run the crew (routes to correct agent based on intent)
    result = crew.run(task)
    return result
