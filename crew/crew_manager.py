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
try:
    import google.generativeai as genai
except Exception:
    genai = None
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
        log.warning("GEMINI_API_KEY not set in env (set it or in Streamlit secrets). LLM calls may fail.")
        return False
    if genai is None:
        log.warning("google.generativeai package not available; LLM calls disabled.")
        return False
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        return True
    except Exception as e:
        log.warning("Failed to configure generativeai: %s", e)
        return False

ensure_genai_configured()

class Agent:
    def __init__(self, name, tools=None, handler=None):
        """Handler may be a callable or an object exposing .analyze/.generate methods.

        If `handler` is supplied, Agent.run will delegate to it. Otherwise Agent will
        use the prompt templates + google.generativeai (if available).
        """
        self.name = name
        self.tools = tools or {}
        self.handler = handler
        cfg = load_config()
        ag_cfg = cfg.get("agents", {}).get(name, cfg.get("llm_defaults", {}))
        self.model = ag_cfg.get("model", cfg.get("llm_defaults", {}).get("model"))
        self.temperature = ag_cfg.get("temperature", cfg.get("llm_defaults", {}).get("temperature", 0.0))
        self.prompt_template = PROMPTS.get(name, PROMPTS.get("UnderstandingAgent"))

    def run(self, query, retrieved_context=""):
        # Delegate to provided handler if available
        if self.handler:
            try:
                # Handler can be a simple callable
                if callable(self.handler):
                    return self.handler(query, retrieved_context)
                # Or an object with analyze/generate
                if hasattr(self.handler, "analyze"):
                    return self.handler.analyze(query, retrieved_context)
                if hasattr(self.handler, "generate"):
                    return self.handler.generate(query, retrieved_context)
                # fallback to str
                return str(self.handler)
            except Exception as e:
                log.exception("Agent handler error for %s: %s", self.name, e)
                return f"Agent handler error: {e}"

        # No handler — fall back to LLM via prompt templates
        prompt = self.prompt_template.format(context=retrieved_context, query=query)
        if genai is None:
            log.error("No generative AI package available and no handler for agent %s", self.name)
            return "LLM unavailable"
        try:
            model = genai.GenerativeModel(self.model)
            resp = model.generate_content(prompt, temperature=self.temperature)
            return resp.text if hasattr(resp, "text") else str(resp)
        except Exception as e:
            log.error(f"LLM call failed for agent {self.name}: {e}")
            return f"LLM error: {e}"

# small registry factory
def create_agent(name, tools=None, handler=None):
    return Agent(name, tools=tools or {}, handler=handler)
