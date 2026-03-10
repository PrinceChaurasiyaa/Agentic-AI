import streamlit as st
from chatbot_backend import workflow
from langchain_core.messages import HumanMessage

st.title("GRAV!NCE", text_alignment="center")
st.markdown("Your Friendly Chatbot", text_alignment="center")


if 'messages' not in st.session_state:
    st.session_state.messages=[]

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('How can I assists you ...')

if user_input:
    # User side handling
    st.session_state.messages.append({"role": "user" ,"content": user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    # Gravince Side Handling
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking...", show_time=True):
            gravince = st.write_stream(
            message_chunk.content for message_chunk , metadata in workflow.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config = {'configurable': {'thread_id': "thread-1"}},
                stream_mode='messages'
            )
        )
    st.session_state.messages.append({"role": "assistant", "content": gravince})