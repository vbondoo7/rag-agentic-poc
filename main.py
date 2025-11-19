# main.py
import os
import streamlit as st
import yaml
from logger import setup_logging
from ai_agents.db import ChatDB
from tools.embedder import Embedder
import ai_agents.architect_agent as architect_agent
from ai_agents.architect_agent import run_agent_sync
from concurrent.futures import ThreadPoolExecutor
from ai_agents.sdk_tools import search_vector
import json
import time

# Backwards-compatible rerun helper (some Streamlit versions lack experimental_rerun)
def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            pass
    if hasattr(st, "rerun"):
        try:
            st.rerun()
            return
        except Exception:
            pass
    # Best-effort fallback: set a refresh flag and stop execution so user can refresh manually
    st.session_state["_needs_refresh"] = True
    st.stop()
import logging
from dotenv import load_dotenv

load_dotenv()
logger = setup_logging()
logger.info("🚀 Starting Agentic Architect AI (Streamlit)")

# Load config
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)

# Ensure dirs
os.makedirs(CONFIG["app"]["persist_dir"], exist_ok=True)
os.makedirs(CONFIG["app"]["metadata_dir"], exist_ok=True)
os.makedirs(os.path.dirname(CONFIG["app"]["db_path"]), exist_ok=True)

# DB init
chat_db = ChatDB(CONFIG["app"]["db_path"])

st.set_page_config(page_title=CONFIG["ui"]["title"], layout="wide")
st.title(CONFIG["ui"]["title"])
st.write(CONFIG["ui"]["description"])

# default values (will be editable in left pane)
repo_path_default = CONFIG["app"]["sample_codebase_dir"]
persist_dir_default = CONFIG["app"]["persist_dir"]

rebuild_index = False

# Main layout: left history, center chat + input, right details
left, center, right = st.columns([1, 5, 1])

# Ensure we start with 'New Chat' on first page load (do not auto-select previous chat)
if not st.session_state.get("app_initialized"):
    st.session_state["selected_chat"] = None
    st.session_state.setdefault("draft_messages", [])
    st.session_state["app_initialized"] = True

with left:
    # New Chat at top (ChatGPT-like)
    # Icon-enhanced New Chat for quick start
    if st.button("➕ New Chat", key="new_chat_top"):
        st.session_state["selected_chat"] = None
        st.session_state["draft_messages"] = []

    # Settings expander below New Chat
    with st.expander("Settings", expanded=False):
        repo_path = st.text_input("Repository / docs folder:", repo_path_default)
        persist_dir = st.text_input("Chroma persist directory:", persist_dir_default)
        rebuild_index = st.button("Rebuild Vector Index")

    st.markdown("---")
    st.subheader("Chat history")
    # Add search control to filter chat history
    search_val = st.text_input("Search chats", value="", key="chat_search")
    chats = chat_db.get_all_chats()
    if search_val and search_val.strip():
        sq = search_val.strip().lower()
        chats = [c for c in chats if (c[1] and sq in c[1].lower()) or (c[2] and sq in c[2].lower())]

    # Do not auto-select any chat on first load; app starts new by default

    st.markdown(
        """
        <style>
        /* Left column fixed-height scroll area */
        .left-scroll {height: calc(100vh - 220px); overflow-y: auto; padding: 6px; position:sticky; top:120px}
        .chat-item {padding:8px; border-radius:6px; margin-bottom:6px; background:#ffffff; box-shadow:0 1px 2px rgba(0,0,0,0.03);} 
        .chat-item small {color: #666}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="left-scroll">', unsafe_allow_html=True)
    for cid, q, agent, resp, ts in chats:
        ag_lower = (agent or "").lower()
        if "impact" in ag_lower:
            icon = "🔍"
        elif "blueprint" in ag_lower or "generate" in ag_lower:
            icon = "🧭"
        elif "doc" in ag_lower:
            icon = "📄"
        else:
            icon = "💬"
        label = f"{ts[:19]} {icon} — {agent}"
        # highlight selected chat visually
        is_sel = st.session_state.get("selected_chat") == cid
        with st.container():
            btn = st.button(label, key=f"history_{cid}")
            if btn:
                st.session_state["selected_chat"] = cid
            if q:
                # make snippet smaller, and replace new lines
                snippet = q.strip().replace("\n", " ")
                st.caption(snippet[:80])
            if is_sel:
                st.markdown("<div style='border-left:3px solid #0b5cff;margin-top:-8px;padding-left:6px'></div>", unsafe_allow_html=True)
    if not chats:
        st.info("No chats yet. Click ➕ New Chat to start.")
    st.markdown('</div>', unsafe_allow_html=True)

# Build index if not present or requested
if 'persist_dir' in locals() and (rebuild_index or not os.listdir(persist_dir)):
    st.info("Indexing repository — this may take a while (model load + embeddings).")
    embedder = Embedder(model_name="all-MiniLM-L6-v2", persist_dir=persist_dir)
    embedder.embed_codebase(repo_path)
    st.success("Vector index created/updated.")

with center:
    st.subheader("Talk to your AI Architect")

    # Chat area - show selected chat or draft
    chat_box = st.container()

    # chat bubble CSS — center column like ChatGPT
    st.markdown(
        """
        <style>
        .chat-center {max-width:1000px;margin-left:auto;margin-right:auto;padding:18px 24px}
        .msg {padding:14px;border-radius:12px;margin:8px 0;box-shadow:0 1px 2px rgba(16,24,40,0.03);line-height:1.5;max-width:85%}
        .user {background:linear-gradient(180deg,#0b5cff,#0a4fe0);color:white;margin-left:auto;text-align:right;border-bottom-right-radius:4px}
        .agent {background:#ffffff;color:#0b2f6b;margin-right:auto;text-align:left;border-bottom-left-radius:4px;border:1px solid #eef2ff}
        .msg-meta {font-size:12px;color:#6b7280;margin-top:6px}
        .input-box {border-radius:999px;padding:12px;border:1px solid #e6e9ef}
        .header-title {font-size:40px;font-weight:700;margin-top:8px}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # load messages (include timestamps when available)
    messages_to_render = []
    if st.session_state.get("selected_chat"):
        cid = st.session_state["selected_chat"]
        chat = chat_db.get_chat_by_id(cid)
        messages = chat_db.get_chat_messages(cid)
        for role, msg, t in messages:
            messages_to_render.append((role, msg, t))
    else:
        # drafts are tuples (role, msg) — add None for timestamp
        for role, msg in list(st.session_state.get("draft_messages", [])):
            messages_to_render.append((role, msg, None))

    with chat_box:
        st.markdown('<div class="chat-center">', unsafe_allow_html=True)
        for role, msg, t in messages_to_render:
            ts = f"<div class=\"msg-meta\">{t}</div>" if t else ""
            if role == "user":
                    st.markdown(f"<div class=\"msg user\">🧍‍♂️ {msg}{ts}</div>", unsafe_allow_html=True)
            else:
                    st.markdown(f"<div class=\"msg agent\">🤖 {msg}{ts}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Clear Draft button outside form (so it doesn't also trigger Send)
    if st.button("Clear Draft"):
        st.session_state["draft_messages"] = []
        st.session_state["pending_user_input"] = ""
        safe_rerun()

    # Floating bottom input (ChatGPT-like) - anchored to bottom center
    default_input = st.session_state.get("pending_user_input", "")
    st.markdown(
        """
        <style>
        .floating-form {position:fixed; left:50%; transform:translateX(-50%); bottom:20px; z-index:9999; width:70%;}
        .floating-inner {background:#fff;padding:8px;border-radius:999px;box-shadow:0 6px 18px rgba(0,0,0,0.08);}
        .floating-input .stTextInput>div>div>input{border-radius:999px}
        @media (max-width: 800px) {.floating-form {width:95%;}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.form(key="floating_chat_form", clear_on_submit=False):
        colf1, colf2 = st.columns([15, 1])
        with colf1:
            # Avoid Streamlit accessibility warning: provide a non-empty label but hide it visually
            user_input = st.text_input("Message", value=default_input, placeholder="Ask anything...", key="bottom_input", label_visibility="collapsed")
        with colf2:
            submitted = st.form_submit_button("Send")
        st.markdown("<div class='floating-form'><div class='floating-inner'></div></div>", unsafe_allow_html=True)

    if submitted:
        if not user_input.strip():
            st.warning("Please type a message before sending.")
        else:
            # keep the user's draft visible across reruns
            st.session_state["pending_user_input"] = user_input
            st.session_state.setdefault("draft_messages", []).append(("user", user_input))
            try:
                # Run orchestrator in background thread and show a progress bar + per-agent statuses
                status_container = st.empty()
                progress_bar = st.progress(0)

                with ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(architect_agent.run_agent_sync, user_input, persist_dir)
                    # poll structured status while task runs
                    # prepare log expander once so it doesn't keep stacking
                    log_expander = st.expander("Agent logs (live)", expanded=False)
                    log_placeholder = log_expander.empty()
                    while not future.done():
                        status = architect_agent.get_status()
                        # Support both legacy string and new dict status
                        if isinstance(status, dict):
                            phase = status.get("phase")
                            agents = status.get("agents", [])
                            # compute progress as fraction of agents done
                            total = len(agents) if agents else 0
                            done = sum(1 for a in agents if a.get("status") == "done")
                            pct = int((done / total) * 100) if total else 0
                            progress_bar.progress(min(max(pct, 0), 100))
                            # render agent status list
                            lines = [f"**Status:** {phase or 'Working...'}\n"]
                            for a in agents:
                                st_sym = "✅" if a.get("status") == "done" else ("🟢" if a.get("status") == "running" else "⚪️")
                                lines.append(f"{st_sym} {a.get('name')}: {a.get('status')}")
                            status_container.markdown("\n\n".join(lines))
                            # Indicate that final answer is pending when agents are running
                            if any(a.get("status") in ("pending", "running") for a in agents):
                                status_container.info("Final answer: assembling — partial results may appear. This is not the final response.")
                            # live logs in the right-hand area: show brief snippets
                            logs = status.get("logs", [])
                            if logs:
                                rendered = []
                                for l in logs[-10:]:
                                    try:
                                        log_text = l if isinstance(l, str) else json.dumps(l)
                                    except Exception:
                                        log_text = str(l)
                                    rendered.append(f"<div style='font-family:monospace;background:#f8fafc;padding:6px;border-radius:6px;margin:4px 0'>{log_text}</div>")
                                log_placeholder.markdown("\n".join(rendered), unsafe_allow_html=True)
                        else:
                            # legacy string
                            status_container.info(str(status or "Agent working..."))
                        time.sleep(0.25)
                    res = future.result()

                response_text = res.get("response", "")
                progress_bar.progress(100)
                status_container.success("Final answer ready — partial answers may have appeared above.")

                st.session_state.setdefault("draft_messages", []).append(("agent", response_text))

                if not st.session_state.get("selected_chat"):
                    chat_id = res.get("chat_id")
                    if chat_id:
                        chat_db.add_message(chat_id, "user", user_input)
                        chat_db.add_message(chat_id, "agent", response_text)
                        st.session_state["selected_chat"] = chat_id
                else:
                    cid = st.session_state["selected_chat"]
                    chat_db.add_message(cid, "user", user_input)
                    chat_db.add_message(cid, "agent", response_text)

                # keep the draft visible (user did not ask to auto-clear)
                # refresh UI so left history reflects the new chat
                safe_rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                logger.exception(e)

    # Move chat details into center pane as a collapsible so UI is more like ChatGPT
    with st.expander("Chat details & RAG", expanded=False):
        if st.session_state.get("selected_chat"):
            cid = st.session_state["selected_chat"]
            chat = chat_db.get_chat_by_id(cid)
            messages = chat_db.get_chat_messages(cid)
            st.markdown(f"**Chat ID:** `{cid}`")
            st.markdown(f"**Agent:** {chat[2]}")
            st.markdown(f"**Created:** {chat[4]}")
            st.markdown(f"**Messages:** {len(messages)}")

            # Show the original user query (if present)
            if chat[1]:
                st.markdown("**Original Query**")
                st.write(chat[1])

            if st.button("Show RAG Sources"):
                with st.spinner("Fetching top RAG matches..."):
                    try:
                        docs = search_vector(chat[1], top_k=5, persist_dir=persist_dir)
                        for i, d in enumerate(docs.get("documents", [])):
                            st.markdown(f"**Source {i+1}:**")
                            st.write(d[:1000])
                            md = docs.get("metadatas", [])[i] if docs.get("metadatas") else {}
                            if md:
                                st.write(md)
                    except Exception as e:
                        st.error(f"RAG error: {e}")
        else:
            st.info("Select a chat to see details & RAG sources.")

# Note: Selected chat messages are shown in the center pane only. Right pane is for metadata/RAG.
