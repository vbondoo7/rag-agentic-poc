import os, logging, json, yaml
import google.genai as genai

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

PROMPT = """
You are a senior solution architect. Produce a JSON blueprint for the requested feature/change. It may involve multiple components/services, so please be mindful and detailed.

Context:
{context}

Request:
{query}

Return STRICT JSON:
{{
  "title": "<short title>",
  "originalRequirement": "<original user request>",
  "components": [
    {{ "name": "", "solution_description": "", "interfaces": [], "notes": "", "estimated_effort": <XS|S|M|L|XL|XXL> }}
  ],
  "patterns": ["list of patterns e.g. event-driven"],
  "risks": ["list"],
  "estimated_overall_effort": "<XS|S|M|L|XL|XXL>"
}}
"""

class BlueprintGeneratorAgent:
    def generate(self, query: str, context: str = "") -> str:
        prompt1 = PROMPT.format(context=context or "No context", query=query)
        logger.info("✅ BlueprintGenerator Agent prompt: %s", prompt1)
        try:
            resp = client.models.generate_content(model="gemini-2.5-flash", prompt=prompt1)
            logger.info("✅ BlueprintGenerator Agent resp: %s", resp)
            text = resp.text if resp else "{}"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            text = "{}"
        try:
            json.loads(text)
            return text
        except Exception:
            return text
