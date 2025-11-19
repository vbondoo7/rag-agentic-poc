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
        cfg = load_config()
        ag_cfg = cfg.get("agents", {}).get(name, cfg.get("llm_defaults", {}))
        self.model = ag_cfg.get("model", cfg["llm_defaults"]["model"])
        self.temperature = ag_cfg.get("temperature", cfg["llm_defaults"]["temperature"])
        self.prompt_template = PROMPTS.get(name, PROMPTS.get("UnderstandingAgent"))

    def run(self, query, retrieved_context=""):
        prompt = self.prompt_template.format(context=retrieved_context, query=query)
        try:
            model = genai.GenerativeModel(self.model)
            resp = model.generate_content(prompt, temperature=self.temperature)
            return resp.text if hasattr(resp, "text") else str(resp)
        except Exception as e:
            log.error(f"LLM call failed for agent {self.name}: {e}")
            return f"LLM error: {e}"

# small registry factory
def create_agent(name, tools=None):
    return Agent(name, tools=tools or {})
