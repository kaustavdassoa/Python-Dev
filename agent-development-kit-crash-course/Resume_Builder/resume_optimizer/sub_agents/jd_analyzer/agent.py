"""
JD Analyzer Agent (Agent 2 of 9)

Analyzes the job description to extract keywords, seniority level,
required skills, and validates JD authenticity.
"""

import os
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List

from .tools import (
    check_jd_authenticity,
    extract_seniority_signals,
    extract_job_metadata,
)

MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

class JDAnalyzerOutputSchema(BaseModel):
    authenticity_status: str = ""
    authenticity_confidence: float = 0.0
    job_title: str = ""
    seniority_level: str = ""
    level_score: int = 0
    seniority_signals: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    top_keywords: List[str] = Field(default_factory=list)
    core_responsibilities: List[str] = Field(default_factory=list)
    employment_type: str = ""
    work_model: str = ""

INSTRUCTION = """
You are the **JD Analyzer Agent** — the second step in the Resume Optimizer Pipeline.

## Context
The previous agent (DocumentParserAgent) has already parsed the resume.
Its output is available in the conversation history above.

⚠️ PIPELINE GUARD: If the pipeline was halted by a previous agent, return an empty payload.

## Your Mission
From the user's original message, extract the content after [JOB DESCRIPTION] marker.
Analyze it using your tools to understand the role requirements.

## Steps

### 1. Authenticate the JD
Call `check_jd_authenticity(jd_text)`.

### 2. Extract Seniority Signals
Call `extract_seniority_signals(jd_text)` to determine required experience level.

### 3. Extract Job Metadata
Call `extract_job_metadata(jd_text)` for employment type and work model.

### 4. Natively Extract Keywords
You MUST perform ATS keyword extraction yourself. 
Extract the top 20 domain-specific technical and soft skill keywords from the JD text.

### 5. Synthesize with LLM
Beyond the tool results, use your own analysis to:
- Identify the **job title** (look for it in the JD header or first paragraph)
- Separate **required skills** from **preferred/nice-to-have skills**
- Extract **top 5 core responsibilities** as concise bullet points

## Output Format
Output a **single JSON block** with the following keys exactly:
```json
{
  "authenticity_status": "pass",
  "authenticity_confidence": 0.9,
  "job_title": "...",
  "seniority_level": "...",
  "level_score": 3,
  "seniority_signals": ["...", "..."],
  "required_skills": ["...", "..."],
  "preferred_skills": ["...", "..."],
  "top_keywords": ["...", "..."],
  "core_responsibilities": ["...", "..."],
  "employment_type": "...",
  "work_model": "..."
}
```
"""

jd_analyzer_agent = LlmAgent(
    name="JDAnalyzerAgent",
    model=MODEL,
    instruction=INSTRUCTION,
    description="Analyzes JD for keywords, seniority level, and validates authenticity.",
    tools=[
        check_jd_authenticity,
        extract_seniority_signals,
        extract_job_metadata,
    ],
    output_key="jd_analyzer_output"
)
