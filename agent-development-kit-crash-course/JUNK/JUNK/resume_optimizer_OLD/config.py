"""
Configuration for the Resume Optimizer multi-agent system.
"""

import os
from dataclasses import dataclass

# Using Google AI Studio (set GOOGLE_API_KEY in your .env file)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")


@dataclass
class ResumeOptimizerConfig:
    """Configuration for model selection and runtime parameters.

    Attributes:
        orchestrator_model: Model for the root orchestrator (Gemini Pro).
        worker_model: Model for sub-agents (Gemini Flash).
    """

    # orchestrator_model: str = "gemini-2.5-pro"
    # worker_model: str = "gemini-2.5-flash"
    orchestrator_model: str = "gemini-2.0-flash"
    worker_model: str = "gemini-2.0-flash"


config = ResumeOptimizerConfig()
