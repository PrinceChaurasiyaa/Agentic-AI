from langchain_ollama import ChatOllama
from langchain_core.tools import tool
import requests
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import create_agent

from dotenv import load_dotenv
import os

os.environ['LANGCHAIN_PROJECT'] = 'ReAct Agent'

load_dotenv()

search_tool = DuckDuckGoSearchRun()

@tool
def get_weather_data(city: str) -> str:
  """
  This function fetches the current weather data for a given city
  """
  url = f'https://api.weatherstack.com/current?access_key=f07d9636974c4120025fadf60678771b&query={city}'

  response = requests.get(url)

  return response.json()

llm = ChatOllama(model="llama3.1:8b")

# Step 2: Pull the ReAct prompt from LangChain Hub
#prompt = hub.pull("hwchase17/react")  # pulls the standard ReAct agent prompt

# Step 3: Create the ReAct agent manually with the pulled prompt
agent = create_agent(
    model=llm,
    tools=[search_tool, get_weather_data]
)

# Step 4: Wrap it with AgentExecutor
# agent_executor = agent.invoke(
#     agent=agent,
#     tools=[search_tool, get_weather_data],
#     verbose=True,
#     max_iterations=5
# )

# What is the release date of Dhadak 2?
# What is the current temp of gurgaon
# Identify the birthplace city of Kalpana Chawla (search) and give its current temperature.

# Step 5: Invoke
response = agent.invoke({
  "messages": [("human", "What is the current temp of gurgaon")]
  })
print(response)

print(response['messages'])
print(response['messages'][-1].content)