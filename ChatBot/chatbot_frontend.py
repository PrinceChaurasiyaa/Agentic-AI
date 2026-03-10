import streamlit as st
from chatbot_backend import workflow
from langchain_core.messages import HumanMessage

st.title("GRAV!NCE", text_alignment="center")
st.markdown("Your Friendly Chatbot", text_alignment="center")

CONFIG = {'configurable': {'thread_id': "thread-1"}}

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
    with st.spinner("Thinking...", show_time=True):
        response = workflow.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG) # pyright: ignore[reportArgumentType]
    gravince = response['messages'][-1].content

    st.session_state.messages.append({"role": "assistant", "content": gravince})
    with st.chat_message("assistant"):
        st.text(gravince)