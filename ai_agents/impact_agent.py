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
SYSTEM: You are a Senior Digital Architect and Dev Lead assistant. Your audience is engineering leads, architects and program managers.
Task: Given the repository context and a change request, produce a concise impact assessment listing the services/modules affected, the nature of change, risks, estimated size, and concrete next-steps for implementation and rollout.

Context:
{context}

Change request:
{query}

Requirements:
- Produce a STRICT JSON array of objects (no surrounding text). Validate the JSON against the schema below. If you include examples, wrap them in a top-level "examples" field.
- For each impacted item provide a short, actionable "next_steps" list for engineers and a one-line risk statement for stakeholders.

Output JSON schema (array of objects):
[
    {{
        "name": "<service/module name>",
        "nature": "<what changes - code/config/data/infra>",
        "level": "<minor|medium|major>",
        "tshirt": "<XS|S|M|L|XL|XXL>",
        "justification": "<short reason - 1 sentence>",
        "risks": ["<short risk statements>"],
        "next_steps": ["<implementable step 1>", "<deploy/test/monitor step 2>"],
        "owners": ["<team or role>"],
        "sources": ["<code paths or documents>"]
    }}
]

Keep entries brief (max 5 bullets in next_steps). Prioritize high-impact items first.
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
        # sanitize common markdown fences before parsing
        try:
            cleaned = text.strip()
            # remove ```json ... ``` or ``` ... ``` fences
            if cleaned.startswith("```") and cleaned.count("```") >= 2:
                # take content between first and last fence
                parts = cleaned.split("```")
                # find non-empty middle part
                for p in parts:
                    p = p.strip()
                    if p and not p.lower().startswith("json"):
                        cleaned = p
                        break
            # also strip leading/trailing ``` if present
            cleaned = cleaned.strip('`').strip()
            json.loads(cleaned)
            return cleaned
        except Exception:
            return json.dumps([{
                "name": "unknown",
                "nature": text,
                "level": "unknown",
                "tshirt": "M",
                "justification": "could not parse LLM output",
                "sources": []
            }])
