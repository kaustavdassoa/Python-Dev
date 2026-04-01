import os
from google.adk.agents import LlmAgent

# Load prompt
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "parser_prompt.txt")
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    _PARSER_INSTRUCTION = f.read()

parser_agent = LlmAgent(
    name="parser_agent",
    model="gemini-2.0-flash",
    instruction=_PARSER_INSTRUCTION,
    description=(
        "Parses a raw PL/SQL stored procedure and extracts structured information: "
        "procedure name, parameters (name, type, direction), local variable declarations, "
        "and the raw procedure body."
    ),
    output_key="parsed_plsql",
)
