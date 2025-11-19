# agents/impact_agent.py
import google.generativeai as genai
import os, logging, json, yaml

# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

PROMPT = """
You are a solution architect assistant. Given context and a change request, list impacted modules.

Context:
{context}

Change request:
{query}

Output STRICT JSON array of objects:
[
  {{
    "name": "<service/module name>",
    "nature": "<what changes>",
    "level": "<minor|medium|major>",
    "tshirt": "<XS|S|M|L|XL|XXL>",
    "justification": "<short reason>",
    "sources": ["<paths>"]
  }}
]
"""

class ImpactAnalyzerAgent:
    def analyze(self, query: str, context: str = "") -> str:
        prompt = PROMPT.format(context=context or "No context", query=query)
        logger.info("✅ ImpactAnalyzer Agent prompt: %s", prompt)
        try:
            #resp = genai.generate_text(model="gemini-2.5-flash", input=prompt) if GEMINI_API_KEY else None
            # Configure the API key
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Load the model
            model = genai.GenerativeModel(CONFIG["llm_mapping"]["impact_agent"])
            # Generate content from the model
            resp = model.generate_content(prompt)
            # Access the generated text
            #resp = response.text
            logger.info("✅ ImpactAnalyzer Agent resp: %s", resp)
            text = resp.text if resp else "[]"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            text = "[]"
        # try to validate JSON, fallback to message
        try:
            json.loads(text)
            return text
        except Exception:
            return json.dumps([{
                "name": "unknown",
                "nature": text,
                "level": "unknown",
                "tshirt": "M",
                "justification": "could not parse LLM output",
                "sources": []
            }])
