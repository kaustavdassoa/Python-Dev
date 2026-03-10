from google.adk.agents import LlmAgent
song_agent = LlmAgent(
    name="song_agent",
    model="gemini-2.5-flash",
    instruction="You are a lyricist. When asked, write a short, creative song on the topic given by the user.",
    description="An agent that writes songs",
)