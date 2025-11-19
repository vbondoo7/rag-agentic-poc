# ai_agents/doc_generator_agent.py
import os
import logging, yaml
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)
    
class DocGeneratorAgent:
    """
    Generates markdown/text documentation from codebase context.
    Uses Google's Gemini via the official google-generativeai SDK.
    """

    def __init__(self, output_dir: str = "generated_docs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(CONFIG["llm_mapping"]["doc_agent"])

    def generate(self, user_input: str, context: str) -> str:
        """
        Generate markdown documentation file and return the short summary text.
        """
        try:
            logger.info("🧠 Generating documentation for user query...")

            prompt = f"""
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
            logger.info("✅ DocGenerator Agent prompt: %s", prompt)
            resp = self.model.generate_content(prompt)
            logger.info("✅ DocGenerator Agent resp: %s", resp)
            text = resp.text if resp else "[]"

            filename = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("# Generated Documentation\n\n")
                f.write(text)

            logger.info("✅ Documentation saved at: %s", filepath)
            return f"Documentation generated successfully: {filepath}\n\n{text[:2000]}"

        except Exception as e:
            logger.exception("❌ Doc generation failed: %s", e)
            return f"Documentation generation failed: {e}"
