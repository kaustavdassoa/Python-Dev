"""
Document Parser Agent (Agent 1 of 9)

Parses the user's resume from PDF, DOCX, or plain text.
Checks resume completeness before allowing the pipeline to proceed.
"""

import os
from google.adk.agents import LlmAgent
from .tools import parse_resume_file
from .prompts import INSTRUCTION

MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

document_parser_agent = LlmAgent(
    name="DocumentParserAgent",
    model=MODEL,
    instruction=INSTRUCTION,
    description="Parses resume text from state or file path and checks completeness.",
    tools=[parse_resume_file],
    output_key="document_parser_output",
)
