# ai_agents/doc_generator_agent.py
import os
import logging, yaml
from datetime import datetime
import google.genai as genai
from dotenv import load_dotenv
from langsmith.run_helpers import traceable
from ai_agents.requirements_agent import GEMINI_API_KEY
load_dotenv()

logger = logging.getLogger(__name__)
# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class DocGeneratorAgent:
    """
    Generates markdown/text documentation from codebase context.
    Uses Google's Gemini via the official google-generativeai SDK.
    """

    def __init__(self, output_dir: str = "generated_docs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Configure Gemini
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        #genai.configure(api_key=api_key)
        #self.model = genai.GenerativeModel(CONFIG["llm_mapping"]["doc_agent"])

    @traceable(
    name="DocGeneratorAgent",
    metadata={"agent_type": "analysis", "model": "gemini-3.5-flash"})
    def generate(self, user_input: str, context: str) -> str:
        """
        Generate markdown documentation file and return the short summary text.
        """
        try:
            logger.info("🧠 Generating documentation for user query...")

            prompt1 = f"""
You are a senior solution architect and technical writer.
Write a clean, structured markdown documentation based on:

User request:
{user_input}

Context (from codebase or retrieved documents):
{context[:6000]}

Structure your output with sections:
- Overview
- Components or Modules
- APIs or Interfaces (if any)
- Dependencies / Integrations
- Example / Usage
- Recommendations
"""
            logger.debug("DocGenerator Agent final prompt: %s", prompt1)
            #resp = self.model.generate_content(prompt)
            #model = genai.GenerativeModel(CONFIG["llm_mapping"]["doc_agent"])
            #resp = client.models.generate_content(model, prompt)
            resp = call_gemini(prompt1)

            logger.info("DocGenerator Agent resp: %s", resp)
            text = resp.text if resp else "[]"

            filename = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("# Generated Documentation\n\n")
                f.write(text)

            logger.info("Documentation saved at: %s", filepath)
            return f"Documentation generated successfully: {filepath}\n\n{text[:2000]}"

        except Exception as e:
            logger.exception("Doc generation failed: %s", e)
            return f"Documentation generation failed: {e}"

@traceable(name="Gemini-Call")
def call_gemini(prompt):
    return client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )