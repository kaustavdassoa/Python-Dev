from google.adk.agents import LlmAgent
story_agent = LlmAgent(
    name="story_agent",
    model="gemini-2.5-flash",
    instruction="You are a storyteller. When asked, write a short, engaging story on the topic given by the user.",
    description="An agent that writes stories",
)