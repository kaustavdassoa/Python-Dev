"""
GapAnalyzerAgent — Sub-agent that compares JD requirements against the
candidate's master experience and produces a structured gap analysis.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from ..config import config
from ..prompts import GAP_ANALYZER_PROMPT
from ..tools import retrieve_master_experience


gap_analyzer = Agent(
    name="gap_analyzer",
    model=config.worker_model,
    description=(
        "Analyzes the gap between a Job Description's requirements and the "
        "candidate's master experience. Produces a structured report of "
        "STRONG MATCH, PARTIAL MATCH, and GAP items."
    ),
    instruction=GAP_ANALYZER_PROMPT,
    tools=[FunctionTool(retrieve_master_experience)],
    output_key="gap_analysis",
)
