from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
import sqlite3
from datetime import datetime

# ======================================Tool Import Integration ===============================
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import ToolNode, tools_condition

from dotenv import load_dotenv

load_dotenv()

model = ChatOllama(model="llama3.1:8b", disable_streaming=False)

# ======================================Tool Integration ===============================
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """

    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}
    
tools = [search_tool, calculator]
llm_with_tools = model.bind_tools(tools)

# =================================== State ===================================
class ChatbotState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
# ================================== Node =======================================
def chat_node(state: ChatbotState):
    prompt = state['messages']
    response = llm_with_tools.invoke(prompt)
    return {'messages': [response]}

tools_node = ToolNode(tools)

# ======================================= Database =====================================
connection = sqlite3.connect(database='gravince.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=connection)

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS thread_metadata (
               thread_id TEXT PRIMARY KEY,
               title TEXT,
               created_at TEXT)
""")

connection.commit()

# ======================================= Graph Connections ================================
graph = StateGraph(ChatbotState)

# Add Nodes
graph.add_node('chat_node', chat_node)

#add tool nodes
graph.add_node("tools", tools_node)

# Add edges
graph.add_edge(START, 'chat_node')
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge('tools', 'chat_node')

workflow = graph.compile(checkpointer=checkpointer)

# ====================================== Dynamic Chat Title =====================================
def generate_chat_title(user_message:str) -> str:
    title_prompt = f"Generate a short 2 or max 3 word chat title for this message: '{user_message}'. Reply with ONLY the title, no punctuation or explanation."
    response = model.invoke([HumanMessage(content=title_prompt)])
    return response.content.strip()[:30]

# ====================================== Database Utility Functions ==============================
def save_thread_metadata(thread_id, title, label):
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO thread_metadata (thread_id, title, created_at)
        VALUES (?, ?, ?)
        """,
        (str(thread_id), title, label)
    )
    connection.commit()

def retrieve_all_threads():
    cursor = connection.cursor()

    rows = cursor.execute(
        "SELECT thread_id, title, created_at FROM thread_metadata ORDER BY created_at"
    ).fetchall()

    threads = []

    for row in rows:
        threads.append({
            "id": row[0],
            "title":row[1],
            "label": row[2]
        })
    
    return threads
    

# def retrieve_all_threads():
#     all_threads = set()
#     for checkpoint in checkpointer.list(None):
#         all_threads.add(checkpoint.config['configurable']['thread_id'])
#     return list(all_threads)


