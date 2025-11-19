# main.py
import os
import streamlit as st
import yaml
from logger import setup_logging
from ai_agents.db import ChatDB
from tools.embedder import Embedder
from ai_agents.architect_agent import run_agent_sync
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

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    repo_path = st.text_input("Repository / docs folder:", CONFIG["app"]["sample_codebase_dir"])
    persist_dir = st.text_input("Chroma persist directory:", CONFIG["app"]["persist_dir"])
    rebuild_index = st.button("Rebuild Vector Index")

# Build index if not present or requested
if rebuild_index or not os.listdir(persist_dir):
    st.info("Indexing repository — this may take a while (model load + embeddings).")
    embedder = Embedder(model_name="all-MiniLM-L6-v2", persist_dir=persist_dir)
    embedder.embed_codebase(repo_path)
    st.success("Vector index created/updated.")

# Main layout: left history, center chat + response
left, center = st.columns([1, 3])

with left:
    st.subheader("Chat history")

    chats = chat_db.get_all_chats()

    # Create a scrollable container
    chat_container = st.container()
    with chat_container:
        st.markdown(
            """
            <style>
            .scrollable-chat {
                max-height: 550px;
                overflow-y: auto;
                padding-right: 10px;
                border: 1px solid #44444422;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="scrollable-chat">', unsafe_allow_html=True)
        for cid, q, agent, resp, ts in chats:
            label = f"{ts[:19]} | {agent}"
            #with st.expander(label):
            #st.markdown(f"**User:** {q}")
              #  st.markdown(f"**Agent ({agent}):**")
               # st.markdown(resp)
            if st.button(f"{ts[:19]} | {agent}", key=f"chat_{cid}"):
                st.session_state["selected_chat"] = cid
        st.markdown("</div>", unsafe_allow_html=True)

with center:
    st.subheader("Talk to your AI Architect - your intelligent system orchestrator")
    user_input = st.text_area("Type your query (Allowed intents: impact/blueprint/understanding/documentation):", height=150)
    if st.button("Submit"):
        if not user_input.strip():
            st.warning("Please enter your query.")
        else:
            with st.spinner("Agent is working..."):
                try:
                    res = run_agent_sync(user_input, persist_dir=persist_dir)
                    chat_id = res.get("chat_id")
                    if chat_id:
                        chat_db.add_message(chat_id, "user", user_input)
                        chat_db.add_message(chat_id, "agent", res.get("response", ""))
                        st.success(f"Agent: {res.get('agent')} — Chat saved (ID={chat_id})")
                    st.session_state["selected_chat"] = chat_id
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.exception(e)
        #if not user_input.strip():
         #   st.warning("Please enter your query.")
        #else:
         #   with st.spinner("Agent executing — this may call Gemini or other LLMs and RAG..."):
          #      try:
           #         res = run_agent_sync(user_input, persist_dir=persist_dir)
            #    except Exception as e:
             #       st.error(f"Agent error: {e}")
              #      #st.stop()
            #if res.get("chat_id"):
             #   st.success(f"Agent: {res.get('agent')} — chat saved: {res.get('chat_id')}")
              #  logger.info(f"Agent: {res.get('agent')} — Chat saved: {res.get('chat_id')}")   
            #else:
             #   st.error("Agent error — see logs.")
            #st.markdown("**Response:**")
            #st.code(res.get("response", ""), language="json")

# --- MODAL-LIKE CHAT DISPLAY ---
# --- MODAL POPUP FOR SELECTED CHAT ---
if "selected_chat" in st.session_state and st.session_state["selected_chat"]:
    chat_id = st.session_state["selected_chat"]
    chat = chat_db.get_chat_by_id(chat_id)
    messages = chat_db.get_chat_messages(chat_id)

    # 🔹 Use a real modal instead of expander
    with st.modal(f"🧠 Chat #{chat_id} — {chat[2]}"):
        st.markdown(f"**📅 Created:** {chat[4]}")

        for role, msg, t in messages:
            if role == "user":
                st.markdown(f"🧍‍♂️ **User:** {msg}")
            else:
                st.markdown(f"🤖 **Agent:** {msg}")

        st.divider()

        # 🔹 Add a Close button that resets modal state
        if st.button("Close Chat"):
            st.session_state["selected_chat"] = None
            st.rerun()
