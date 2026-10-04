from google.adk.agents import LlmAgent
from dotenv import load_dotenv
import os


# Load .env from the package directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

if not os.getenv("GOOGLE_API_KEY"):
    print("Warning: GOOGLE_API_KEY not set. Add it to .env")

# Define the agent
root_agent = LlmAgent(
    name="history_agent",
    model="gemini-2.5-flash",
    instruction="When asked about a topic, summarize the answer in bullet points and provide a 5 lines crisp summary at the end",
    description="An agent that helps with history lessions",
)
