# agents/requirements_agent.py
import google.generativeai as genai
import os
import logging, yaml
from ai_agents.sdk_tools import search_vector

# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)
    
logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

PROMPT = """
You are a requirements intent detector and short analyzer. Given the user's request and supporting context (from code/docs), produce the intent classification and a 1-line summary.
Possible intents are: impact, blueprint, understanding, documentation, generic.
Request:
{query}

Context snippets:
{context}

Return JSON: {{ "intent": "<impact|blueprint|understanding|documentation|generic>", "summary": "<one-line summary>" }}
Be strict JSON only.
"""

class RequirementsAnalyzer:
    def get_intent(self, query: str, context: str = "") -> dict:
        prompt = PROMPT.format(query=query, context=context)
        logger.info("✅ RequirementsAnalyzer Agent prompt: %s", prompt)
        try:
            #resp = genai.generate_text(model="gemini-2.5-flash", input=prompt) if GEMINI_API_KEY else None
            # Configure the API key
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Load the model
            model = genai.GenerativeModel(CONFIG["llm_mapping"]["requirement_agent"])
            # Generate content from the model
            resp = model.generate_content(prompt)
            # Access the generated text
            #resp = response.text
            logger.info("✅ RequirementsAnalyzer Agent resp: %s", resp)
            text = resp.text if resp else '{"intent":"generic","summary":"(simulated)"}'
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            text = '{"intent":"generic","summary":"(failed to call LLM)"}'
        import json
        try:
            return json.loads(text)
        except Exception:
            # best effort fallback
            intent = "generic"
            if "impact" in query.lower(): intent = "impact"
            if "blueprint" in query.lower(): intent = "blueprint"
            if "document" in query.lower(): intent = "documentation"
            return {"intent": intent, "summary": text}
