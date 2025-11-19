# main.py
import os
import yaml
import streamlit as st
import logging
from datetime import datetime
from dotenv import load_dotenv

# your project modules (must exist as in your repo)
from ai_agents.db import ChatDB
from tools.embedder import Embedder
from ai_agents.architect_agent import run_agent_sync  # agent must NOT write to DB
from logger import setup_logging

load_dotenv()
logger = setup_logging()  # your logger setup
logger.info("Starting Agentic Architect AI (Streamlit UI)")

# --- LOAD CONFIG (keep your original approach) ---
with open("config.yaml", "r") as fh:
    CONFIG = yaml.safe_load(fh)

# Ensure directories from config exist (use same keys as your config.yaml)
persist_dir = CONFIG["app"].get("persist_dir", "chroma_db")
metadata_dir = CONFIG["app"].get("metadata_dir", "metadata")
sample_codebase_dir = CONFIG["app"].get("sample_codebase_dir", "./sample_codebase")
db_path = CONFIG["app"].get("db_path", "data/chats.db")

os.makedirs(persist_dir, exist_ok=True)
os.makedirs(metadata_dir, exist_ok=True)
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# --- DB INIT (Chat history storage) ---
chat_db = ChatDB(db_path)

# --- Streamlit page config ---
st.set_page_config(page_title=CONFIG["ui"].get("title", "Agentic Architect AI"), layout="wide")
st.title(CONFIG["ui"].get("title", "Agentic Architect AI"))
if CONFIG["ui"].get("description"):
    st.write(CONFIG["ui"].get("description"))

# --- Sidebar settings (repo path, persist_dir) ---
with st.sidebar:
    st.header("Settings")
    repo_path = st.text_input("Repository / docs folder:", value=sample_codebase_dir)
    persist_dir = st.text_input("Chroma persist directory:", value=persist_dir)
    rebuild_index = st.button("Rebuild Vector Index (force)")

# --- Build embeddings / vector DB if needed ---
# We call your Embedder.embed_codebase(repo_path) — make sure Embedder exists and works.
if rebuild_index or not os.listdir(persist_dir):
    st.info("Indexing repository — this may take a while (SentenceTransformers loads first time).")
    try:
        embedder = Embedder(model_name=CONFIG["app"].get("embed_model", "all-MiniLM-L6-v2"),
                            persist_dir=persist_dir)
        embedder.embed_codebase(repo_path)
        st.success("Vector index created/updated.")
        logger.info("Vector index built at %s", persist_dir)
    except Exception as e:
        st.error(f"Failed to build embeddings: {e}")
        logger.exception("Embedding build failed")

# --- Session state initialization ---
if "selected_chat_id" not in st.session_state:
    st.session_state.selected_chat_id = None
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

# --- Left column: Chat list + controls ---
left, center = st.columns([1, 3])

with left:
    st.subheader("Chat history")
    if st.button("➕ New Chat"):
        st.session_state.selected_chat_id = None
        st.session_state.input_text = ""
        # incrementing refresh key ensures UI updates
        st.session_state.refresh_key += 1
        st.rerun()

    # scrollable chat list style
    st.markdown(
        """
        <style>
        .chat-list { max-height: 70vh; overflow-y: auto; padding-right:8px; }
        .chat-item { padding:8px; border-bottom:1px solid #eee; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="chat-list">', unsafe_allow_html=True)

    chats = chat_db.get_all_chats()  # returns list of tuples (id, user_query, agent_name, agent_response, created_at)
    if not chats:
        st.info("No chats yet. Start a new chat from above.")
    else:
        # show most recent first (db already returns desc)
        for cid, q, agent, resp, ts in chats:
            pretty = f"{ts[:19]} — {agent} — {q[:60]}"
            # clicking a chat selects it
            if st.button(pretty, key=f"select_{cid}"):
                st.session_state.selected_chat_id = cid
                st.session_state.refresh_key += 1
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Center column: Chat conversation + input ---
with center:
    st.subheader("Talk to your AI Architect - your intelligent system orchestrator")
    # If a chat is selected, load recent messages (messages table optional; fallback to chat record)
    if st.session_state.selected_chat_id:
        chat = chat_db.get_chat_by_id(st.session_state.selected_chat_id)
        if chat:
            cid, q, agent, resp, ts = chat
            st.markdown(f"**Conversation ID:** {cid} — created: {ts}")
            # try to fetch messages table if available
            try:
                messages = chat_db.get_chat_messages(cid)  # expects list of (role, content, created_at)
            except Exception:
                # fallback: show single chat record
                messages = [("user", q, ts), (agent, resp, ts)]
            for role, content, created_at in messages:
                if role == "user":
                    st.markdown(f"🧑 **You:** {content}")
                else:
                    st.markdown(f"🤖 **{role}:** {content}")
        else:
            st.info("Selected chat not found.")

    else:
        st.info("Start a new conversation or select one from the left.")

    # Input area — use key so Streamlit doesn't complain on changes
    input_area_key = f"user_input_{st.session_state.get('refresh_key',0)}"
    user_input = st.text_area("Your message", value=st.session_state.input_text, key=input_area_key, height=140)

    if st.button("Send"):
        if not user_input.strip():
            st.warning("Please type a message.")
        else:
            # If no chat selected, create chat record first
            if not st.session_state.selected_chat_id:
                chat_id = chat_db.add_chat(user_input, "ArchitectAgent", "")  # initial empty response
                st.session_state.selected_chat_id = chat_id
                logger.info("Created new chat id=%s", chat_id)
            else:
                chat_id = st.session_state.selected_chat_id

            # Save user message to messages table if available; also keep chats table as summary
            try:
                chat_db.add_message(chat_id, "user", user_input)
            except Exception:
                logger.debug("messages table not available or add_message missing, continuing")

            # Call agent (agent should not write DB itself)
            with st.spinner("Agent is analyzing (may call Gemini + RAG)..."):
                try:
                    agent_result = run_agent_sync(user_input, persist_dir=persist_dir)
                    # agent_result expected to be a dict or string — standardize
                    if isinstance(agent_result, dict):
                        agent_resp = agent_result.get("response") or agent_result.get("agent_response") or str(agent_result)
                        agent_name = agent_result.get("agent") or "ArchitectAgent"
                        chat_id_returned = agent_result.get("chat_id", None)
                    else:
                        agent_resp = str(agent_result)
                        agent_name = "ArchitectAgent"
                        chat_id_returned = None
                except Exception as e:
                    agent_resp = f"Agent error: {e}"
                    agent_name = "ArchitectAgent"
                    logger.exception("Agent call failed")

            # Save agent response in messages table and update chats summary
            try:
                chat_db.add_message(chat_id, "agent", agent_resp) 
            except Exception:
                logger.debug("messages table not available or add_message missing, continuing")

            # Update the summary fields in chats table
            chat_db.update_chat_response(chat_id, agent_name, agent_resp)

            # show response
            st.success(f"Agent ({agent_name}) responded.")
            st.markdown("**Response:**")
            st.code(agent_resp)

            # clear input and refresh list
            st.session_state.input_text = ""
            st.session_state.refresh_key += 1
            st.rerun()
