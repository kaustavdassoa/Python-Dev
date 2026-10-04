from google.adk import Agent

# Define the agent
brand_story_agent = Agent(
    name="brand_story_agent",
    model="gemini-2.5-flash",
    description="An agent who creates a brand story on a given topic.",
    instruction="""You are an agent who specializes in creating brand story. Please make sure the story is relevent to current generation and it is limited to 5 lines and crisp in nature""",
)
