from google.adk.agents import LlmAgent
from .sub_agents.joke import joke_agent
from .sub_agents.song import song_agent
from .sub_agents.story import story_agent


# Define the root  agent
root_agent = LlmAgent(
    name="entertainment_agent",
    model="gemini-2.5-flash",
    instruction="""You are a entertainer which uses other available agents to write stories, songs or jokes 
         Instructions:
         - Please greet the user and offer the services you provide and ask for thier choice
         - Based on user preference use of the sub agents to get the output and present to the user""",
    description="An agent which entertains people with songs, stories or jokes",
    sub_agents=[song_agent, story_agent, joke_agent],
)
