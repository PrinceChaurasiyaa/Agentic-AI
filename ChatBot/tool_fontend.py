import streamlit as st
from tool_backend import workflow, retrieve_all_threads, save_thread_metadata, generate_chat_title
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid
from datetime import datetime

# =================================== Utility functions ============================================
def generate_thread_id():
    thread_id = uuid.uuid4()
    return str(thread_id)

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    #add_thread(st.session_state['thread_id'], user_input)
    st.session_state.messages = []

def chat_label():
    timestamp = datetime.now()
    formated_time = timestamp.strftime("%d %b %Y, %H:%M:%S")
    return formated_time

def add_thread(thread_id, title=""):
    for t in st.session_state['chat_threads']:
        if t['id'] == thread_id:
            return
    
    label = chat_label()
        
    st.session_state['chat_threads'].append({
        "id": thread_id,
        "label": label,
        "title": title
    })

    save_thread_metadata(thread_id, title, label)

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

# if 'chat_threads' not in st.session_state:
#     st.session_state['chat_threads'] = [
#         {"id": t, "title": "", "label": chat_label()}
#         for t in retrieve_all_threads()
#     ]


if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()


# ==================================Input UI ====================================================

user_input = st.chat_input('Ask anything')
if user_input:
    if not any(t['id'] == st.session_state['thread_id'] for t in st.session_state['chat_threads']):
        with st.spinner("Processing...", show_time=True):
            dynamic_title = generate_chat_title(user_input)
            add_thread(st.session_state['thread_id'], dynamic_title)


# ==================================== Sidebar UI ======================================================
with st.sidebar:
    st.title("History")

    if st.button("New Chat"):
        reset_chat()

    st.title("Your Converstions")

    for chat_thread in st.session_state['chat_threads'][::-1]:
        label = chat_thread['label']
        short_label = label[:6] +", "+ label[12:18]
        if st.button(f"{chat_thread['title']} | {short_label}", 
                     key=str(chat_thread['id']), 
                     use_container_width=True):
            st.session_state['thread_id'] = chat_thread['id']
            try:
                messages = load_conversation(chat_thread['id'])
                
                temp_messages = []

                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        temp_messages.append({
                            "role": 'user', 
                            "content": msg.content
                        })

                    elif isinstance(msg, AIMessage) and msg.content:
                        temp_messages.append({
                            "role": 'assistant', 
                            "content": msg.content
                    })
    
                    
                st.session_state.messages = temp_messages
            except:
                st.error("No Chat Available.")
                st.toast("No Chat Available.")
                st.session_state['chat_error'] = True

            

# ===================================== Main UI ======================================================
if st.session_state.get('chat_error'):
    st.info("Lets Start our First Conversions.")
    st.session_state['chat_error'] = False

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if user_input:
    # User side handling
    st.session_state.messages.append({"role": "user" ,"content": user_input})
    with st.chat_message('user'):
        st.markdown(user_input)
    
    # Gravince Side Handling
    CONFIG = {
        'configurable': {'thread_id': st.session_state['thread_id']},
        'metadata': {
            'thread_id': st.session_state['thread_id']
        },
        'run_name': 'chat_turn'
    }
    
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in workflow.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f" Using `{tool_name}` …", expanded=False
                        )
                    else:
                        status_holder["box"].update(
                            label=f" Using `{tool_name}` …",
                            state="running",
                            expanded=False,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        gravince = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

        # gravince = st.write_stream(
        #     message_chunk.content for message_chunk , metadata in workflow.stream(
        #         {'messages': [HumanMessage(content=user_input)]},
        #         config = CONFIG,
        #         stream_mode='messages'
        #     )
        # )

    st.session_state.messages.append({"role": "assistant", "content": gravince})