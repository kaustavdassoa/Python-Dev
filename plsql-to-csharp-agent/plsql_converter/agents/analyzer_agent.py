import os
from google.adk.agents import LlmAgent

# Load prompt
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "analyzer_prompt.txt")
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    _ANALYZER_INSTRUCTION = f.read()

analyzer_agent = LlmAgent(
    name="analyzer_agent",
    model="gemini-2.0-flash",
    instruction=_ANALYZER_INSTRUCTION,
    description=(
        "Analyzes the parsed PL/SQL structure and annotates its logical components: "
        "SQL statements (SELECT/INSERT/UPDATE/DELETE), control flow constructs "
        "(IF/ELSE, loops), exception handling blocks, and flags unsupported constructs "
        "such as cursors and dynamic SQL."
    ),
    output_key="analyzed_plsql",
)
