import streamlit as st
from chatbot_backend import workflow
from langchain_core.messages import HumanMessage
import uuid
from datetime import datetime

# =================================== Utility functions ============================================
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state.messages = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return workflow.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']


# ===================================== Header UI =====================================================
st.title("GRAV!NCE", text_alignment="center")
st.markdown("Your Friendly Chatbot", text_alignment="center")

# ===================================== Session State ===============================================
if 'messages' not in st.session_state:
    st.session_state.messages=[]

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []


# ==================================Input UI ====================================================

user_input = st.chat_input('How can I assists you ...')
if user_input:
    add_thread(st.session_state['thread_id'])

# ==================================== Sidebar UI ======================================================
with st.sidebar:
    st.title("History")

    if st.button("New Chat"):
        reset_chat()

    st.title("Your Converstions")
    for chat_thread in st.session_state['chat_threads'][::-1]:
        if st.button(str(chat_thread)):
            st.session_state['thread_id'] = chat_thread
            messages = load_conversation(chat_thread)

            temp_messages = []

            for msg in messages:
                if isinstance(msg, HumanMessage):
                    role="user"
                else:
                    role="assistant"
                temp_messages.append({"role": role, "content": msg.content})
            st.session_state.messages = temp_messages

# ===================================== Main UI ======================================================
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.text(message['content'])

if user_input:
    # User side handling
    st.session_state.messages.append({"role": "user" ,"content": user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    # Gravince Side Handling
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    
    with st.chat_message("assistant"):
        # ======================= Streaming =======================================================
        gravince = st.write_stream(
            message_chunk.content for message_chunk , metadata in workflow.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config = CONFIG,
                stream_mode='messages'
            )
        )
    st.session_state.messages.append({"role": "assistant", "content": gravince})