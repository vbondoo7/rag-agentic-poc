# crew/crew_manager.py
"""
Simple Crew-like agent framework used locally.
An Agent has:
 - name
 - tools (callable functions returning (text, docs))
 - prompt template
 - model settings
 - run(query, context) -> returns string

This is intentionally small and synchronous for Streamlit.
"""

from ai_agents import prompts
from ai_agents.prompts import PROMPTS
from google import generativeai as genai_stub  # placeholder if google package not present
import google.generativeai as genai
from logger import log
import yaml
import os

CFG_PATH = "config.yaml"

def load_config():
    import yaml
    with open(CFG_PATH, "r", encoding="utf8") as fh:
        return yaml.safe_load(fh)

def ensure_genai_configured():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY not set in env (set it or in Streamlit secrets). Agents will error on LLM calls.")
        return False
    genai.configure(api_key=GEMINI_API_KEY)
    return True

ensure_genai_configured()

class Agent:
    def __init__(self, name, tools=None):
        self.name = name
        self.tools = tools or {}
        cfg = load_config() or {}
        # support either an explicit `agents` mapping or a legacy `llm_defaults` structure
        agents_cfg = cfg.get("agents", {})
        ag_cfg = agents_cfg.get(name, {})
        # fallback to llm_mapping.default or a sensible hard-coded default
        default_model = cfg.get("llm_mapping", {}).get("default", "gemini-2.5-flash")
        self.model = ag_cfg.get("model", default_model)
        self.temperature = ag_cfg.get("temperature", cfg.get("llm_defaults", {}).get("temperature", 0.0))
        self.prompt_template = PROMPTS.get(name, PROMPTS.get("UnderstandingAgent"))

    def run(self, query, retrieved_context=""):
        prompt = self.prompt_template.format(context=retrieved_context, query=query)
        try:
            # If no LLM key is configured, return a helpful fallback for local testing.
            if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
                log.info("GEMINI_API_KEY not set — returning retrieved context as fallback response")
                # Return a short summary / echo so callers can see retrieval is working.
                snippet = (retrieved_context[:1000] + "...") if len(retrieved_context) > 1000 else retrieved_context
                return f"[LLM disabled] Retrieved context (truncated):\n{snippet}"

            model = genai.GenerativeModel(self.model)
            resp = model.generate_content(prompt, temperature=self.temperature)
            return resp.text if hasattr(resp, "text") else str(resp)
        except Exception as e:
            log.error(f"LLM call failed for agent {self.name}: {e}")
            return f"LLM error: {e}"

# small registry factory
def create_agent(name, tools=None):
    return Agent(name, tools=tools or {})
