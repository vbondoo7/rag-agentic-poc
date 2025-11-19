# agents/blueprint_agent.py
import google.generativeai as genai
import os, logging, json, yaml

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)

# Ensure dirs
os.makedirs(CONFIG["app"]["persist_dir"], exist_ok=True)
os.makedirs(CONFIG["app"]["metadata_dir"], exist_ok=True)
os.makedirs(os.path.dirname(CONFIG["app"]["db_path"]), exist_ok=True)


PROMPT = """
SYSTEM: You are a Senior Digital Architect producing an actionable blueprint for engineering teams and program managers. Target audience: architects, tech leads, and dev leads.
Task: Using the provided context and request, produce a STRICT JSON blueprint that is implementation-ready. Be specific about components, interfaces, data changes, migration steps, testing strategy, deployment plan and observability.

Context:
{context}

Request:
{query}

Return STRICT JSON matching the shape below (no surrounding commentary):
{
    "title": "<short title>",
    "originalRequirement": "<original user request>",
    "summary": "<one-line summary for stakeholders>",
    "components": [
        {
            "name": "",
            "solution_description": "",
            "interfaces": ["<API/event/topic/interface details>"],
            "data_changes": ["<schema/migration notes>"],
            "notes": "",
            "estimated_effort": "<XS|S|M|L|XL|XXL>",
            "owners": ["<team or role>"],
            "risk_mitigation": ["<short mitigation steps>"]
        }
    ],
    "patterns": ["list of patterns e.g. event-driven"],
    "testing_strategy": ["unit/integration/e2e/chaos/verifications"],
    "deployment_plan": ["canary/blue-green/rollout steps"],
    "observability": ["metrics/logs/tracing to add"],
    "rollback_plan": "<short rollback steps>",
    "estimated_overall_effort": "<XS|S|M|L|XL|XXL>"
}

Notes:
- Keep component descriptions concise but precise (include required interfaces and data changes).
- Provide migration steps where schema or contract changes are required.
- Include testing and observability actions so teams can validate rollout.
"""

class BlueprintGeneratorAgent:
    def generate(self, query: str, context: str = "") -> str:
        prompt = PROMPT.format(context=context or "No context", query=query)
        logger.info("✅ BlueprintGenerator Agent prompt: %s", prompt)
        try:
            #resp = genai.generate_text(model="gemini-2.5-flash", input=prompt) if GEMINI_API_KEY else None
            # Configure the API key
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Load the model
            model = genai.GenerativeModel(CONFIG["llm_mapping"]["blueprint_agent"])
            # Generate content from the model
            resp = model.generate_content(prompt)
            # Access the generated text
            #resp = response.text
            logger.info("✅ BlueprintGenerator Agent resp: %s", resp)
            text = resp.text if resp else "{}"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            text = "{}"
        # Try to sanitize typical markdown fences and return valid JSON when possible
        try:
            cleaned = text.strip()
            if cleaned.startswith("```") and cleaned.count("```") >= 2:
                parts = cleaned.split("```")
                for p in parts:
                    p = p.strip()
                    if p and not p.lower().startswith("json"):
                        cleaned = p
                        break
            cleaned = cleaned.strip('`').strip()
            json.loads(cleaned)
            return cleaned
        except Exception:
            return text
