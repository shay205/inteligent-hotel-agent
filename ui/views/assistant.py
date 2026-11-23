import uuid

import streamlit as st

from hotel_agent.config import HOTEL_NAME
from ui.components import hero, rerun, show_table
import pandas as pd

SUGGESTED = [
    "How much is a deluxe room?",
    "Is a family room available tomorrow?",
    "Which rooms have a sea view?",
    "Suggest a room under $150 for 2 guests",
    "Do you offer a spa or airport transfers?",
    "What time is check-in?",
]


def _init_state(ctx) -> None:
    if "chat_session" not in st.session_state:
        st.session_state["chat_session"] = uuid.uuid4().hex[:12]
        st.session_state["chat_context"] = {}
        st.session_state["chat_messages"] = [{
            "role": "assistant", "intent": "", "confidence": None,
            "content": f"Hello! I'm the virtual assistant for **{HOTEL_NAME}**. Ask me about prices, availability, "
                       "facilities, bookings or services."}]


def render(ctx) -> None:
    hero("Your hotel concierge", "Ask naturally about rooms, availability, dining, spa experiences and your stay.")
    _init_state(ctx)
    session = st.session_state["chat_session"]

    top = st.columns([5, 1])
    with top[0]:
        st.markdown("<p class='assistant-status'><span></span> Concierge online</p>",
                    unsafe_allow_html=True)
    with top[1]:
        if st.button("New chat", key="new_chat", width="stretch"):
            for key in ("chat_session", "chat_context", "chat_messages"):
                st.session_state.pop(key, None)
            rerun()

    if len(st.session_state["chat_messages"]) == 1:
        st.caption("Popular questions")
        cols = st.columns(3)
        for i, question in enumerate(SUGGESTED):
            if cols[i % 3].button(question, key=f"sugg_{i}", width="stretch"):
                st.session_state["pending_question"] = question

    for msg in st.session_state["chat_messages"]:
        avatar = ":material/concierge:" if msg["role"] == "assistant" else ":material/person:"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("intent"):
                st.caption(f"Detected intent: {msg['intent']} (confidence {msg['confidence']})")

    prompt = st.chat_input("Ask about rooms, prices, availability or services...",
                           submit_mode="disable")
    if not prompt:
        prompt = st.session_state.pop("pending_question", None)
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state["chat_messages"].append({"role": "user", "content": prompt, "intent": "", "confidence": None})
        with st.status(":shimmer[Concierge is checking live hotel information]", state="running") as status:
            try:
                response = ctx.chatbot.respond(prompt, st.session_state["chat_context"])
            except Exception as exc:  # the chat must never crash the app
                response = None
                reply, intent, conf = f"Sorry, something went wrong while answering ({exc}). Please try rephrasing.", "ERROR", 0.0
            else:
                reply, intent, conf = response.text, response.intent, response.confidence
            status.update(label="Your answer is ready", state="complete")
        with st.chat_message("assistant"):
            st.markdown(reply)
            st.caption(f"Detected intent: {intent} (confidence {conf})")
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply, "intent": intent, "confidence": conf})
        ctx.conversations.save_message(session, "user", prompt)
        ctx.conversations.save_message(session, "assistant", reply, intent)

    with st.expander("Saved conversation history (from the database)"):
        rows = ctx.conversations.recent_messages(60)
        if not rows:
            st.caption("No saved messages yet.")
        else:
            df = pd.DataFrame(rows)[["created_at", "session_id", "role", "intent", "message"]]
            show_table(df.rename(columns={"created_at": "Time", "session_id": "Session", "role": "Role",
                                          "intent": "Intent", "message": "Message"}))