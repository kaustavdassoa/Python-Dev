import os
from google.adk.agents import LlmAgent

# Load prompt
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "converter_prompt.txt")
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    _CONVERTER_INSTRUCTION = f.read()

converter_agent = LlmAgent(
    name="converter_agent",
    model="gemini-2.0-flash",
    instruction=_CONVERTER_INSTRUCTION,
    description=(
        "Converts the parsed and analyzed PL/SQL structure into a compilable C# method body. "
        "Maps Oracle types to C# types, converts control flow, wraps SQL as raw string variables, "
        "converts exception blocks to try/catch, and flags unsupported constructs with TODO comments."
    ),
    output_key="csharp_code",
)
