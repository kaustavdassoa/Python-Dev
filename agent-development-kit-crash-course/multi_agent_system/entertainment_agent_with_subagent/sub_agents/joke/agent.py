from google.adk.agents import LlmAgent
joke_agent = LlmAgent(
    name="joke_agent",
    model="gemini-2.5-flash",
    instruction="You are a comedian. When asked, tell a funny, original joke on the topic given by the user.",
    description="An agent that tells jokes",
)