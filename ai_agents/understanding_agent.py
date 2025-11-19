# agents/understanding_agent.py
import google.generativeai as genai
import os, logging, yaml
from ai_agents.sdk_tools import search_vector

# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

PROMPT = """
You are an expert software architect. Use the context and relevant all files in the main repo and service specific folders to explain the module/service.

Context:
{context}

User query:
{query}

Return bullet points covering only if there has been a very generic ask from user for a particular service/module/component, including:
- System/component purpose
- Major relationships
- Key challenges
- Any gotchas
- Improvement areas - tech debt, architecture, code quality, performance, security etc. with details

Otherwise focus on the user's specific query and DO NOT Include the above aspects in your response, be very specific while responding.

Return as plain text.
"""

class UnderstandingAgent:
    def analyze(self, query: str, context: str = "") -> str:
        prompt = PROMPT.format(context=context or "No context", query=query)
        logger.info("✅ Understanding Agent prompt: %s", prompt)
        try:
            #resp = genai.generate_text(model="gemini-2.5-flash", input=prompt) if GEMINI_API_KEY else None
            # Configure the API key
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Load the model
            model = genai.GenerativeModel(CONFIG["llm_mapping"]["understanding_agent"])
            # Generate content from the model
            resp = model.generate_content(prompt)
            # Access the generated text
            #resp = response.text
            logger.info("✅ Understanding Agent resp: %s", resp)
            return resp.text if resp else "(simulated) Understanding result"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            return f"Error generating understanding: {e}"
