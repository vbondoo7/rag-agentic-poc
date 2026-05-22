import os, logging, json, yaml
import google.genai as genai

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

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
        prompt1 = PROMPT.format(context=context or "No context", query=query)
        logger.info("✅ ImpactAnalyzer Agent prompt: %s", prompt1)
        try:
            resp = client.models.generate_content(model="gemini-2.5-flash", prompt=prompt1)
            logger.info("✅ ImpactAnalyzer Agent resp: %s", resp)
            text = resp.text if resp else "[]"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            text = "[]"
        try:
            json.loads(text)
            return text
        except Exception:
            return text
