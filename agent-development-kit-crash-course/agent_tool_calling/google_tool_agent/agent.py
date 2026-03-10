from google.adk.agents import Agent
from google.adk.tools import google_search


root_agent = Agent(
    name="google_news_agent",
    model="gemini-2.5-flash",
    instruction="Look for all the latest news in the internet and provide a crisp summary based on the topic",
    description="An agent that uses Google Search to fetch up-to-date news",
    tools=[google_search],
)
