from google.adk.agents import ParallelAgent
from .sub_agents.brand_story import brand_story_agent
from .sub_agents.hashtag import hashtag_agent


# Define the root  agent
root_agent = ParallelAgent(
    name="marketing_agent",
    #model="gemini-2.5-flash",
    description="Runs multiple parallel agents to create a brand marketing inputs",
    sub_agents=[brand_story_agent,hashtag_agent],
)
