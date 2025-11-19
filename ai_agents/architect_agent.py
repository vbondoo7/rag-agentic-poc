# ai_agents/architect_agent.py
import logging
from ai_agents.requirements_agent import RequirementsAnalyzer
from ai_agents.understanding_agent import UnderstandingAgent
from ai_agents.impact_agent import ImpactAnalyzerAgent
from ai_agents.blueprint_agent import BlueprintGeneratorAgent
from ai_agents.doc_generator_agent import DocGeneratorAgent
from ai_agents.sdk_tools import search_vector, detect_intent
from ai_agents.db import ChatDB

logger = logging.getLogger(__name__)

# Initialize agents
req_analyzer = RequirementsAnalyzer()
understanding_agent = UnderstandingAgent()
impact_agent = ImpactAnalyzerAgent()
blueprint_agent = BlueprintGeneratorAgent()
doc_agent = DocGeneratorAgent()
db = ChatDB()


def run_agent_sync(user_input: str, persist_dir: str = "chroma_db"):
    """
    Orchestrates all sub-agents based on detected intent.
    Performs:
      - Intent detection
      - Context retrieval (RAG)
      - Delegation to correct agent
      - Persists chat result
    """
    try:
        logger.info("🚀 Received input: %s", user_input)

        # Step 1: Detect intent
        intent_info = req_analyzer.get_intent(user_input)
        intent = intent_info.get("intent", detect_intent(user_input))
        logger.info("🧠 Detected intent: %s", intent)

        # Step 2: Retrieve RAG context
        rag = search_vector(user_input, top_k=5, persist_dir=persist_dir)
        docs = rag.get("documents", [[]])[0] if isinstance(rag.get("documents"), list) else []
        metadatas = rag.get("metadatas", [[]])[0] if isinstance(rag.get("metadatas"), list) else []

        context_pieces = []
        for i, doc in enumerate(docs):
            src = metadatas[i].get("source") if i < len(metadatas) else None
            context_pieces.append(f"Source: {src}\n{doc}")
        context = "\n\n---\n\n".join(context_pieces)[:30000] if context_pieces else "No relevant documents found."
        logger.info("📚 Context prepared with %d docs.", len(context_pieces))

        # Step 3: Route to correct agent
        if intent == "impact":
            out = impact_agent.analyze(user_input, context)
            agent_name = "ImpactAnalyserAgent"
        elif intent == "blueprint":
            out = blueprint_agent.generate(user_input, context)
            agent_name = "BlueprintGeneratorAgent"
        elif intent == "documentation":
            out = doc_agent.generate(user_input, context)
            agent_name = "DocGeneratorAgent"
        elif intent == "understanding":
            out = understanding_agent.analyze(user_input, context)
            agent_name = "UnderstandingAgent"
        else:
            out = understanding_agent.analyze(user_input, context)
            agent_name = "GenericAgent"

        # Step 4: Persist chat to DB
        chat_id = db.add_chat(
            user_query=user_input,
            agent_name=agent_name,
            agent_response=out
        )
        logger.info("💾 Chat saved: id=%s, agent=%s", chat_id, agent_name)

        # Step 5: Return structured response
        return {"chat_id": chat_id, "agent": agent_name, "response": out}

    except Exception as e:
        logger.exception("❌ Agent run failed: %s", e)
        return {"chat_id": None, "agent": "error", "response": f"Agent error: {e}"}
