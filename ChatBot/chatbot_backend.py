from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver

model = ChatOllama(model="deepseek-r1:8b", disable_streaming=False)

from langgraph.graph.message import add_messages

class ChatbotState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    

def chat_node(state: ChatbotState):
    prompt = state['messages']
    response = model.invoke(prompt)
    return {'messages': [response]}


checkpointer = MemorySaver()
graph = StateGraph(ChatbotState)

# Add Nodes
graph.add_node('chat_node', chat_node)

# Add edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

workflow = graph.compile(checkpointer=checkpointer)