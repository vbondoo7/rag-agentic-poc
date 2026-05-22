import os, logging, yaml
import google.genai as genai

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class DocGeneratorAgent:
    def generate(self, user_input: str, context: str) -> str:
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
        try:
            logger.info("🧠 Generating documentation for user query...")
            resp = client.models.generate_content(model="gemini-2.5-flash", prompt=prompt1)
            logger.info("✅ DocGenerator Agent resp: %s", resp)
            return resp.text if resp else "(no response)"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            return f"Error generating documentation: {e}"
