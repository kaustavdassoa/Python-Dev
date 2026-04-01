import os
from google.adk.agents import LlmAgent

# Load prompt
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "validator_prompt.txt")
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    _VALIDATOR_INSTRUCTION = f.read()

validator_agent = LlmAgent(
    name="validator_agent",
    model="gemini-2.5-flash-lite",
    instruction=_VALIDATOR_INSTRUCTION,
    description=(
        "Performs a lightweight structural validation of the generated C# method body. "
        "Checks for: valid method signature, balanced braces, and any leaked PL/SQL syntax "
        "(e.g., ':=', 'BEGIN', 'END;'). Returns the validated code with a PASSED or WARNINGS status."
    ),
    output_key="validated_csharp",
)
