"""
ImpactWriterAgent — Sub-agent that rewrites resume bullets in the
Google XYZ format: "Accomplished [X] as measured by [Y], by doing [Z]".
"""

from google.adk.agents import Agent

from ..config import config
from ..prompts import IMPACT_WRITER_PROMPT


impact_writer = Agent(
    name="impact_writer",
    model=config.worker_model,
    description=(
        "Rewrites resume bullet points in the Google XYZ format for maximum "
        "ATS optimization. Uses only verified facts from the master experience."
    ),
    instruction=IMPACT_WRITER_PROMPT,
    output_key="optimized_bullets",
)
