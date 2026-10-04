"""
Root orchestrator for the Resume Optimizer multi-agent system.

ResumeOptimizer is an LlmAgent (Gemini Pro) that:
1. Receives a Job Description from the user
2. Retrieves the candidate's master experience
3. Delegates gap analysis to GapAnalyzerAgent
4. Delegates bullet writing to ImpactWriterAgent
5. Runs a hallucination audit on the final output
6. Returns the audited, ATS-optimized resume bullets
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from dotenv import load_dotenv
import os

from .config import config
from .prompts import ROOT_ORCHESTRATOR_PROMPT
from .sub_agents import gap_analyzer, impact_writer
from .tools import retrieve_master_experience, audit_hallucination

# Load environment variables from .env file
load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("⚠️  Warning: GOOGLE_API_KEY not found in environment. "
          "Set it in resume_optimizer/.env")


# --- ROOT AGENT DEFINITION ---

resume_optimizer = Agent(
    name="resume_optimizer",
    model=config.orchestrator_model,
    description=(
        "Root orchestrator that coordinates the full resume optimization "
        "pipeline: experience retrieval → gap analysis → impact bullet "
        "writing → hallucination audit."
    ),
    instruction=ROOT_ORCHESTRATOR_PROMPT,
    sub_agents=[gap_analyzer, impact_writer],
    tools=[
        FunctionTool(retrieve_master_experience),
        FunctionTool(audit_hallucination),
    ],
)

# ADK requires a module-level `root_agent` to be discoverable by `adk web`
root_agent = resume_optimizer
