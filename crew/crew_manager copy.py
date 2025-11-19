# crew/crew_manager.py
import os
from crewai import Agent, Task, Crew
from logs.logger import get_logger
from db.chat_db import save_message
from uuid import uuid4
from typing import List
import google.generativeai as genai

logger = get_logger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("Gemini API key not set! Please export GEMINI_API_KEY or add to secrets.toml.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# === Agent Definitions ===
def get_crew_agents() -> List[Agent]:
    """Create CrewAI agents with different expertise."""
    agents = [
        Agent(
            role="Architect",
            goal="Understand functional architecture and dependencies.",
            backstory="An enterprise architect who maps microservices and interactions.",
            verbose=True,
            allow_delegation=True,
        ),
        Agent(
            role="ImpactAnalyst",
            goal="Perform impact assessment of new requirements.",
            backstory="An experienced solution impact analyst skilled at evaluating code changes and dependencies.",
            verbose=True,
            allow_delegation=False,
        ),
        Agent(
            role="BlueprintDesigner",
            goal="Generate solution blueprint with flows, integration points, and risk summary.",
            backstory="A design expert that creates architecture diagrams and textual blueprints.",
            verbose=True,
            allow_delegation=False,
        ),
    ]
    return agents


def create_crew():
    """Instantiate the full crew."""
    agents = get_crew_agents()
    crew = Crew(
        agents=agents,
        process="hierarchical",
        verbose=True,
    )
    logger.info("Crew initialized with %d agents", len(agents))
    return crew


def run_task_with_crew(prompt: str, chat_id: str) -> str:
    """
    Execute user prompt through the Crew framework.
    Each agent processes it sequentially (Architect → Impact → Blueprint).
    """
    try:
        crew = create_crew()
        task = Task(
            description=prompt,
            agent=crew.agents[0],
            expected_output="A structured JSON summarizing architecture, impacts, and blueprint suggestions."
        )
        results = crew.kickoff([task])

        output = results[0].output_text if results and hasattr(results[0], "output_text") else str(results)
        logger.info("Crew run completed for chat %s", chat_id)
        save_message(chat_id, "user", "User", prompt)
        save_message(chat_id, "assistant", "Crew", output)
        return output
    except Exception as e:
        logger.error("Crew task failed: %s", e)
        return f"Error: {e}"
