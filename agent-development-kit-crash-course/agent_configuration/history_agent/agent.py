from google.adk.agents import LlmAgent
from google.genai import types

# Define the agent
root_agent = LlmAgent(
    name="history_agent",
    model="gemini-2.5-flash",
    instruction="When asked about a topic, summarize the answer in bullet points and provide a 5 lines crisp summary at the end",
    description="An agent that helps with history lessions",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2, 
        max_output_tokens=4000,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]
    )
)
