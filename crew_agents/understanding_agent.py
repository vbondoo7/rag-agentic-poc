import os, logging, yaml
import google.genai as genai

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

PROMPT = """
You are an expert software architect. Use the context and relevant all files in the main repo and service specific folders to explain the module/service.

Context:
{context}

User query:
{query}

Return bullet points covering only if there has been a very generic ask from user for a particular service/module/component, including:
- System/componchatent purpose
- Major relationships
- Key challenges
- Any gotchas
- Improvement areas - tech debt, architecture, code quality, performance, security etc. with details

Otherwise focus on the user's specific query and DO NOT Include the above aspects in your response, be very specific while responding.

Return as plain text.
"""

class UnderstandingAgent:
    def analyze(self, query: str, context: str = "") -> str:
        prompt1 = PROMPT.format(context=context or "No context", query=query)
        logger.info("Understanding Agent prompt: %s", prompt1)
        try:
            resp = client.models.generate_content(model="gemini-3.5-flash", prompt=prompt1)
            logger.info("Understanding Agent resp: %s", resp)
            return resp.text if resp else "(simulated) Understanding result"
        except Exception as e:
            logger.exception("Gemini error: %s", e)
            return f"Error generating understanding: {e}"
