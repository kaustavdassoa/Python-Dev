"""Configuration for the Resume Evaluator agent."""

import os
from dataclasses import dataclass

# Use Google AI Studio (set GOOGLE_API_KEY in .env)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")


@dataclass
class ResumeOptimizerConfig:
    """Model configuration.

    Attributes:
        model: The Gemini model to use for the agent.
    """

    model: str = "gemini-2.5-flash"


config = ResumeOptimizerConfig()
