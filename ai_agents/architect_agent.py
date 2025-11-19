
# ai_agents/architect_agent.py
import logging
from ai_agents.requirements_agent import RequirementsAnalyzer
from ai_agents.understanding_agent import UnderstandingAgent
from ai_agents.impact_agent import ImpactAnalyzerAgent
from ai_agents.blueprint_agent import BlueprintGeneratorAgent
from ai_agents.doc_generator_agent import DocGeneratorAgent
from ai_agents.sdk_tools import search_vector, detect_intent
from ai_agents.db import ChatDB
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

logger = logging.getLogger(__name__)

# Initialize agents
req_analyzer = RequirementsAnalyzer()
understanding_agent = UnderstandingAgent()
impact_agent = ImpactAnalyzerAgent()
blueprint_agent = BlueprintGeneratorAgent()
doc_agent = DocGeneratorAgent()
db = ChatDB()

# Structured status reporting for UI polling
_STATUS = {"phase": None, "agents": [], "logs": []}


def set_status(msg: str):
    """Set a human-readable phase/status string for UI."""
    try:
        _STATUS["phase"] = msg
    except Exception:
        pass


def set_agent_status(agent_name: str, status: str):
    """Set/append status for a named agent (pending, running, done, error)."""
    try:
        agents = _STATUS.setdefault("agents", [])
        # find existing
        for a in agents:
            if a.get("name") == agent_name:
                a["status"] = status
                return
        # not found, append
        agents.append({"name": agent_name, "status": status})
    except Exception:
        pass

def append_log(msg: str):
    """Append a short log entry to the status for UI streaming."""
    try:
        lst = _STATUS.setdefault("logs", [])
        # keep logs bounded
        # store the original object (dict or string) so UI can render structured logs
        lst.append(msg)
        if len(lst) > 200:
            lst[:] = lst[-200:]
    except Exception:
        pass

def get_logs():
    try:
        return _STATUS.get("logs", [])
    except Exception:
        return []


def _resolve_agent_name(agent_callable):
    """Return a friendly agent name for a callable.

    If the callable is a bound method on an agent instance, prefer the instance's
    class name (e.g., `ImpactAnalyzerAgent`) so the UI shows which agent ran.
    Otherwise fall back to the callable __name__ or string form.
    """
    try:
        # bound method -> __self__ refers to instance; include method name for clarity
        if hasattr(agent_callable, "__self__") and agent_callable.__self__ is not None:
            inst = agent_callable.__self__
            method = getattr(agent_callable, "__name__", "<call>")
            return f"{inst.__class__.__name__}.{method}"
        # plain function
        name = getattr(agent_callable, "__name__", None)
        if name:
            return name
        return str(agent_callable)
    except Exception:
        return str(agent_callable)


def get_status():
    """Return the structured status dict for UI consumption.

    Older UI code may expect a string; callers should handle both.
    """
    return _STATUS


def _build_context(user_input: str, persist_dir: str):
    rag = search_vector(user_input, top_k=5, persist_dir=persist_dir)
    docs = rag.get("documents", [[]])[0] if isinstance(rag.get("documents"), list) else []
    metadatas = rag.get("metadatas", [[]])[0] if isinstance(rag.get("metadatas"), list) else []

    context_pieces = []
    for i, doc in enumerate(docs):
        src = metadatas[i].get("source") if i < len(metadatas) else None
        context_pieces.append(f"Source: {src}\n{doc}")
    context = "\n\n---\n\n".join(context_pieces)[:30000] if context_pieces else "No relevant documents found."
    return context, len(context_pieces)


AGENT_PIPELINES = {
    "impact": {"strategy": "parallel", "agents": [understanding_agent.analyze, impact_agent.analyze], "synthesis": True},
    "blueprint": {"strategy": "sequence", "agents": [understanding_agent.analyze, impact_agent.analyze, blueprint_agent.generate], "synthesis": False},
    "documentation": {"strategy": "sequence", "agents": [doc_agent.generate], "synthesis": False},
    "understanding": {"strategy": "sequence", "agents": [understanding_agent.analyze], "synthesis": False},
    "generic": {"strategy": "parallel", "agents": [understanding_agent.analyze], "synthesis": False},
}


def _attempt_refinement(agent_callable, user_input, context, prev_outputs, max_retries=2):
    """Try to call the agent up to `max_retries` times, passing previous outputs as extra context."""
    attempt = 0
    last_out = None
    while attempt <= max_retries:
        try:
            augmented_context = context + "\n\nPrevious agent outputs:\n" + ("\n".join(prev_outputs) if prev_outputs else "")
            out = agent_callable(user_input, augmented_context)
            last_out = out
            # Quick quality heuristic: non-empty and not the 'could not parse' fallback
            if out and not out.strip().lower().startswith("could not parse"):
                return out
        except Exception:
            pass
        attempt += 1
    return last_out or ""


def run_agent_sync(user_input: str, persist_dir: str = "chroma_db"):
    """
    Enhanced orchestrator supporting pipeline execution (sequence/parallel), optional synthesis,
    and simple iterative refinement when outputs look incomplete.
    Returns a combined response and persists chat history.
    """
    try:
        logger.info("🚀 Received input: %s", user_input)

        # Step 1: Detect intent
        set_status("Detecting intent")
        intent_info = req_analyzer.get_intent(user_input)
        intent = intent_info.get("intent", detect_intent(user_input))
        logger.info("🧠 Detected intent: %s", intent)

        # Step 2: Build RAG context
        set_status("Building RAG context")
        context, num_docs = _build_context(user_input, persist_dir)
        logger.info("📚 Context prepared with %d docs.", num_docs)

        # Select pipeline (allow special-case: user asked for an "impact assessment document")
        pipeline = AGENT_PIPELINES.get(intent, AGENT_PIPELINES.get("generic"))
        lower_input = (user_input or "").lower()
        if "impact assessment" in lower_input or ("impact" in lower_input and "document" in lower_input) or ("generate" in lower_input and "impact" in lower_input):
            pipeline = {"strategy": "sequence", "agents": [understanding_agent.analyze, impact_agent.analyze, doc_agent.generate], "synthesis": False}
        strategy = pipeline.get("strategy")
        agent_calls = pipeline.get("agents", [])

        results = []

        # Initialize per-agent statuses
        _STATUS["agents"] = []
        for ag in agent_calls:
            name = _resolve_agent_name(ag)
            set_agent_status(name, "pending")
            append_log({"agent": name, "status": "pending", "output": ""})

        # Execute agents
        if strategy == "parallel":
            set_status("Running agents (parallel)")
            with ThreadPoolExecutor(max_workers=len(agent_calls) or 1) as ex:
                futures = {ex.submit(agent, user_input, context): agent for agent in agent_calls}
                for fut in as_completed(futures):
                    agent = futures[fut]
                    name = _resolve_agent_name(agent)
                    set_agent_status(name, "running")
                    append_log({"agent": name, "status": "running", "output": ""})
                    try:
                        out = fut.result()
                        set_agent_status(name, "done")
                        append_log({"agent": name, "status": "done", "output": out[:400]})
                    except Exception as e:
                        logger.exception("Agent %s failed: %s", name, e)
                        out = f"Agent {name} error: {e}"
                        set_agent_status(name, "error")
                        append_log({"agent": name, "status": "error", "output": str(e)})
                    results.append((name, out))
        else:  # sequence
            set_status("Running agents (sequence)")
            prev_outputs = []
            for agent in agent_calls:
                name = _resolve_agent_name(agent)
                set_agent_status(name, "running")
                append_log({"agent": name, "status": "running", "output": ""})
                try:
                    out = agent(user_input, context)
                    set_agent_status(name, "done")
                    append_log({"agent": name, "status": "done", "output": out[:400]})
                except TypeError:
                    # try without context
                    try:
                        out = agent(user_input)
                        set_agent_status(name, "done")
                        append_log({"agent": name, "status": "done", "output": out[:400]})
                    except Exception as e:
                        logger.exception("Agent sequence failure: %s", e)
                        out = f"Agent error: {e}"
                        set_agent_status(name, "error")
                        append_log({"agent": name, "status": "error", "output": str(e)})
                except Exception as e:
                    logger.exception("Agent sequence failure: %s", e)
                    out = f"Agent error: {e}"
                    set_agent_status(name, "error")
                    append_log({"agent": name, "status": "error", "output": str(e)})
                results.append((name, out))
                prev_outputs.append(out if isinstance(out, str) else json.dumps(out))

        # Optional synthesis step: when pipeline requests it, ask the blueprint agent to synthesize findings
        final_response = None
        if pipeline.get("synthesis"):
            set_status("Synthesizing final response")
            # combine results into a single context and call blueprint_agent to synthesize
            synth_context = context + "\n\nAgent outputs:\n" + "\n\n".join([f"=={name}==\n{out}" for name, out in results])
            try:
                final_response = blueprint_agent.generate(user_input, synth_context)
            except Exception as e:
                logger.exception("Synthesis failed: %s", e)
                final_response = "\n\n".join([out for _, out in results])
        else:
            # Concatenate agent outputs as the final response
            final_response = "\n\n".join([f"[{name}]\n{out}" for name, out in results])

        # Quick iterative refinement: if response seems too short or contains known error markers, retry main agent
        if (not final_response or len(final_response) < 20) and agent_calls:
            main_agent = agent_calls[-1]
            logger.info("🔁 Refining response by re-invoking %s", _resolve_agent_name(main_agent))
            refined = _attempt_refinement(main_agent, user_input, context, [r for _, r in results], max_retries=2)
            if refined:
                final_response = refined

        set_status("Finalizing and persisting chat")
        # Persist chat (store combined response)
        agent_name = ",".join([_resolve_agent_name(a) for a in agent_calls])
        chat_id = db.add_chat(user_query=user_input, agent_name=agent_name, agent_response=final_response)
        logger.info("💬 Chat added — ID=%s | Agent=%s", chat_id, agent_name)

        set_status("Done")
        return {"chat_id": chat_id, "agent": agent_name, "response": final_response}

    except Exception as e:
        logger.exception("❌ Agent run failed: %s", e)
        return {"chat_id": None, "agent": "error", "response": f"Agent error: {e}"}

