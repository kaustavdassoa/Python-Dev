from google.adk import Agent
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper



root_agent = Agent(
    name="wiki_agent",
    model="gemini-2.5-flash",
    description="An agent who answers questions using Wikipedia.",
    instruction="""Research the topic provided by the user using the tools available and 
    share the information with the user.""",
    tools=[
        LangchainTool(
            tool=WikipediaQueryRun(
                api_wrapper=WikipediaAPIWrapper()
            )
        )
    ]
)


