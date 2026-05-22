import os
import streamlit as st
from crew_agents.crew_config import run_crew_agent
from crew_agents.sqlite_chat import ChatDB
from crew_agents.langsmith_tracing import log_trace

st.set_page_config(page_title="CrewAI Architect Buddy", layout="wide")
st.title("CrewAI Architect Buddy")

# DB
chat_db = ChatDB()

# Session state
if "selected_chat_id" not in st.session_state:
    st.session_state.selected_chat_id = None
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

left, center = st.columns([1, 3])

with left:
    st.subheader("Chat history")
    if st.button("➕ New Chat"):
        st.session_state.selected_chat_id = None
        st.session_state.input_text = ""
        st.session_state.refresh_key += 1
        st.rerun()
    chats = chat_db.get_all_chats()
    if not chats:
        st.info("No chats yet. Start a new chat from above.")
    else:
        for cid, q, agent, resp, ts in chats:
            pretty = f"{ts[:19]} — {agent} — {q[:60]}"
            if st.button(pretty, key=f"select_{cid}"):
                st.session_state.selected_chat_id = cid
                st.session_state.refresh_key += 1
                st.rerun()

with center:
    st.subheader("Talk to your CrewAI Architect Buddy")
    if st.session_state.selected_chat_id:
        chat = chat_db.get_chat_by_id(st.session_state.selected_chat_id)
        if chat:
            cid, q, agent, resp, ts = chat
            st.markdown(f"**Conversation ID:** {cid} — created: {ts}")
            try:
                messages = chat_db.get_chat_messages(cid)
            except Exception:
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
    input_area_key = f"user_input_{st.session_state.get('refresh_key',0)}"
    user_input = st.text_area("Your message", value=st.session_state.input_text, key=input_area_key, height=140)
    if st.button("Send"):
        if not user_input.strip():
            st.warning("Please type a message.")
        else:
            if not st.session_state.selected_chat_id:
                chat_id = chat_db.add_chat(user_input, "CrewAgent", "")
                st.session_state.selected_chat_id = chat_id
            else:
                chat_id = st.session_state.selected_chat_id
            try:
                chat_db.add_message(chat_id, "user", user_input)
            except Exception:
                pass
            with st.spinner("CrewAI agent is thinking..."):
                agent_result = run_crew_agent(user_input)
                agent_resp = str(agent_result)
                agent_name = "CrewAgent"
                log_trace(user_input, agent_name, agent_resp)
            try:
                chat_db.add_message(chat_id, "agent", agent_resp)
            except Exception:
                pass
            chat_db.get_chat_by_id(chat_id)
            st.success(f"Agent ({agent_name}) responded.")
            st.markdown("**Response:**")
            st.code(agent_resp)
            st.session_state.input_text = ""
            st.session_state.refresh_key += 1
            st.rerun()
