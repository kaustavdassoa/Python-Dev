from google.adk.agents import LlmAgent

hashtag_agent = LlmAgent(
    name="hashtag_agent",
    model="gemini-2.5-flash",
    instruction="""Create a hashtag for the given topic and make sure it is relevent to current generation""",
    description="An agent which is good with creating hashtags for any given topic",
)
