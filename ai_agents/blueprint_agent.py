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
    {{ "name": "", "solution_description": "", "interfaces": [], "notes": ", "estimated_effort": <XS|S|M|L|XL|XXL>"" }}
  ],
  "patterns": ["list of patterns e.g. event-driven"],
  "risks": ["list"],
  "estimated_overall_effort": "<XS|S|M|L|XL|XXL>"
}}
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
        try:
            json.loads(text)
            return text
        except Exception:
            return text #json.dumps({
                #"title": "Blueprint fallback",
                #"originalRequirement": "" + query +"",
                #"components": [],
                #"patterns": [],
                #"risks": ["LLM output unparsable"],
                #"estimated_effort": "<NONE>"
            #})
