# agents/understanding_agent.py
import google.generativeai as genai
import os, logging, yaml
from ai_agents.sdk_tools import search_vector

# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

PROMPT = """
SYSTEM: You are an expert Software Architect and Senior Dev Lead advisor. Your audience includes architects, tech leads and engineering managers.
Task: Using the supplied context, explain the relevant module/service and answer the user's query with practical, prioritized actions and concerns.

Context:
{context}

User query:
{query}

Behavior / output guidance:
- If the user asks generically about a module/service, return concise bullet points covering: purpose, major relationships, key challenges, known gotchas, and prioritized improvement areas (tech debt, architecture, performance, security). Limit to 6 bullets.
- If the user asks a specific question (e.g., how to implement X, where to change code, migration steps), focus strictly on the requested topic and provide step-by-step actionable guidance for engineers (code locations, tests, rollout notes).
- Where relevant, include one-line recommendations for monitoring/metrics and a short rollback strategy.

Return as plain text (human-readable), with short code-path references where possible.
"""

class UnderstandingAgent:
    def analyze(self, query: str, context: str = "") -> str:
        prompt = PROMPT.format(context=context or "No context", query=query)
        logger.info("✅ Understanding Agent prompt: %s", prompt)
        try:
            #resp = genai.generate_text(model="gemini-2.5-flash", input=prompt) if GEMINI_API_KEY else None
            # Configure the API key
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Load the model
            model = genai.GenerativeModel(CONFIG["llm_mapping"]["understanding_agent"])
            # Generate content from the model
            resp = model.generate_content(prompt)
            # Access the generated text
            #resp = response.text
            logger.info("✅ Understanding Agent resp: %s", resp)
            return resp.text if resp else "(simulated) Understanding result"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            return f"Error generating understanding: {e}"
