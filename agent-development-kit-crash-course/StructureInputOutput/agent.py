from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field


class CountryInput(BaseModel):
    country: str = Field(description="The country to get information about.")

class CapitalOutput(BaseModel):
    capital: str = Field(description="The capital city of the country.")

# Define the agent
root_agent = LlmAgent(
    name="capital_agent",
    model="gemini-2.5-flash",
    instruction="""You are an agent which returns the capital of a country when the country name provided in json format {"country": "Canada"}. If the format is not maintained by user, suggest to use the json format. Respond ONLY with a JSON object matching this exact schema: {json.dumps(CapitalOutput.model_json_schema(), indent=2)} """,
    #instruction="""when shared with a country name, answer with the capital of the country""",
    description="An agent that helps with capital of a country",
    input_schema=CountryInput,
    output_schema=CapitalOutput,
)
