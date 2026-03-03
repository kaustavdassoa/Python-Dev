"""
Resume Evaluator (JSON output) — Single-agent ADK application.

A variant of resume_evaluator that:
  - Extracts text from a PDF resume via the `extract_resume_from_pdf` tool
  - Returns structured JSON output enforced by Pydantic schema
  - Can be invoked as a sub-agent by an orchestrator

Tools:
  - extract_resume_from_pdf : reads a PDF file and returns its text
  - retrieve_master_experience : fallback candidate profile
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from dotenv import load_dotenv
import os

from .config import config
from .tools import extract_resume_from_pdf, retrieve_master_experience

# Load .env from the package directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

if not os.getenv("GOOGLE_API_KEY"):
    print("Warning: GOOGLE_API_KEY not set. Add it to .env")


# ── Pydantic output schema ──────────────────────────────────────────
# Gemini's structured-output mode will guarantee the response conforms
# exactly to this schema — no malformed JSON possible.


class PastExperience(BaseModel):
    """A single work experience entry."""
    company: str = Field(description="Company name")
    role: str = Field(description="Job title / role")
    duration: str = Field(description="Employment period, e.g. 'Jan 2020 - Present'")
    key_accomplishments: list[str] = Field(description="Key accomplishments in this role")


class Education(BaseModel):
    """Education details."""
    degree: str = Field(description="Degree earned")
    university: str = Field(description="University / institution name")
    graduation_year: str = Field(description="Year of graduation")


class StrongMatch(BaseModel):
    """A JD requirement that strongly matches the resume."""
    requirement: str = Field(description="The JD requirement")
    evidence: list[str] = Field(
        description="List of specific evidence items from the resume (company, role, accomplishment)"
    )


class PartialMatch(BaseModel):
    """A JD requirement that partially matches the resume."""
    requirement: str = Field(description="The JD requirement")
    candidate_has: str = Field(description="What the candidate has that is related")
    whats_missing: str = Field(description="What is missing or not demonstrated")


class Gap(BaseModel):
    """A JD requirement not found in the resume."""
    requirement: str = Field(description="The JD requirement")
    notes: str = Field(description="Additional notes about the gap")


class ResumeEvaluation(BaseModel):
    """Complete resume evaluation result."""
    candidate_name: str = Field(description="Full name from the resume")
    candidate_title: str = Field(description="Current or most recent job title")
    total_years_of_experience: int = Field(description="Total years of professional experience")
    skills: list[str] = Field(description="All technical and soft skills found in the resume")
    past_experiences: list[PastExperience] = Field(description="Work experience entries")
    education: Education = Field(description="Education details")
    certifications: list[str] = Field(description="Professional certifications")
    overall_match_score: int = Field(description="Match score as a percentage (0-100)")
    fit_category: str = Field(description="One of: Strong Fit, Moderate Fit, Weak Fit")
    required_matched: str = Field(description="e.g. '8 of 10'")
    nice_to_have_matched: str = Field(description="e.g. '2 of 3'")
    score_calculation: str = Field(description="Show the point breakdown math")
    strong_matches: list[StrongMatch] = Field(description="JD requirements that are strong matches")
    partial_matches: list[PartialMatch] = Field(description="JD requirements that are partial matches")
    gaps: list[Gap] = Field(description="JD requirements not found in the resume")
    key_highlights: list[str] = Field(description="Top 5 highlights from the resume relevant to this role")
    recruiter_recommendation: str = Field(
        description="2-3 sentences: Should this candidate advance? What should the interviewer probe?"
    )


# ── Agent instruction ────────────────────────────────────────────────

INSTRUCTION = """\
You are ResumeEvaluator, an expert talent assessment system built for recruiters.
Given a candidate's resume and a Job Description (JD), you produce a detailed
structured evaluation showing how well the candidate matches the role.

CRITICAL RULES — READ FIRST:
- Be STRICT in matching. A skill is a STRONG MATCH only if the resume explicitly
  demonstrates hands-on experience with that EXACT technology. Similar or adjacent
  technologies count as PARTIAL MATCH, not STRONG MATCH.
- Do NOT assume skills not explicitly stated in the resume.
- Be honest about gaps — recruiters need accurate assessments, not inflated scores.
- For each strong_match, the "evidence" field MUST be a list of strings, where each
  string is one specific piece of evidence (e.g. a specific accomplishment, role, or
  metric from the resume). Never combine multiple pieces of evidence into one string.

## Your Internal Workflow

1. If the user provides a file_path to a PDF, call `extract_resume_from_pdf`
   with that path to get the resume text.
   If NO file path was provided, call the `retrieve_master_experience` tool.

2. Extract the candidate's details from the resume:
   - Full name
   - Current/most recent title
   - Total years of experience
   - List of technical and soft skills
   - List of past experiences (company, role, duration, key accomplishments)
   - Education details
   - Certifications

3. Parse the JD and list every requirement:
   - Technical skills (languages, frameworks, tools, platforms)
   - Years of experience
   - Domain expertise
   - Certifications or education
   - Soft skills (leadership, communication, mentoring)
   - "Nice-to-have" or preferred qualifications (mark these separately)

4. For EACH requirement, classify it:
   - STRONG MATCH: Resume explicitly shows hands-on, demonstrated experience
     with this EXACT skill/technology. Must cite specific evidence.
   - PARTIAL MATCH: Resume shows related but not exact experience (e.g.,
     resume says "React" but JD asks "ReactJS + Redux" — partial, not strong).
   - GAP: Resume does not mention this skill or anything closely related.

5. Calculate match score STRICTLY:
   - Count required items and nice-to-have items separately.
   - Required: STRONG = 1.0 point, PARTIAL = 0.5, GAP = 0.0
   - Nice-to-have: STRONG = 0.5 point, PARTIAL = 0.25, GAP = 0.0
   - Score = (total points earned / maximum possible points) x 100
   - Show the math in the score_calculation field.

6. Extract top 5 highlights from the resume relevant to this specific role.

Scoring thresholds: 80-100% = Strong Fit | 60-79% = Moderate Fit | Below 60% = Weak Fit
"""

resume_evaluator_json_agent = Agent(
    name="resume_evaluator_json",
    model=config.model,
    description=(
        "Evaluates a candidate's resume against a Job Description. "
        "Extracts candidate details and returns a structured JSON evaluation "
        "with match percentage, gap analysis, and recruiter insights. "
        "Accepts a PDF file path and a Job Description as input."
    ),
    instruction=INSTRUCTION,
    tools=[
        FunctionTool(extract_resume_from_pdf),
        FunctionTool(retrieve_master_experience),
    ],
    output_key="evaluation",
    output_schema=ResumeEvaluation,
)

# Alias for standalone use with `adk web`
root_agent = resume_evaluator_json_agent

