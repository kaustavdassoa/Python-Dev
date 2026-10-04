"""
Resume Rewriter Agent (Agent 5 of 9)

The core rewriting engine. Takes the parsed resume structure and
rewrites every section to maximize ATS keyword match and job fit
while preserving original structure and not fabricating experience.
"""

import os
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Optional

MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

class ContactSchema(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""

class ExperienceSchema(BaseModel):
    title: str = ""
    company: str = ""
    dates: str = ""
    bullets: List[str] = Field(default_factory=list)

class EducationSchema(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""

class RewrittenResumeSchema(BaseModel):
    contact: ContactSchema
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class ResumeRewriterOutputSchema(BaseModel):
    rewritten_resume: RewrittenResumeSchema
    changes_summary: List[str] = Field(default_factory=list)
    keywords_injected: List[str] = Field(default_factory=list)
    keywords_not_injectable: List[str] = Field(default_factory=list)

INSTRUCTION = """
You are the **Resume Rewriter Agent** — the fifth and most critical step in the Resume Fit Pipeline.

## Context
- `document_parser_output`: original parsed resume sections
- `jd_analyzer_output`: job title, required skills, top keywords, core responsibilities
- `ats_precheck_output`: missing keywords that must be added, formatting warnings to fix

⚠️ PIPELINE GUARD: If `pipeline_halted` is true in state, return an empty payload without processing.

## Your Mission
Rewrite the resume to maximize ATS keyword match and alignment with the job description.

## ABSOLUTE RULES — Never Break These
1. **Never fabricate.** Only use skills, tools, and experiences mentioned in the original resume.
   - DO NOT add skills that are not in the original
   - DO NOT change job titles (e.g., intern → lead engineer)
   - DO NOT invent companies, dates, or responsibilities
2. **Preserve structure.** Keep the same sections in the same order as the original.
3. **Natural keyword injection.** Insert missing keywords only when they genuinely fit the context.
4. **Upgrade weak verbs.** Replace passive/weak openers.
5. **ATS formatting.** Replace special bullet characters (•, ►, →) with standard hyphens (-).
6. **🚨 UNRELATED EXPERIENCE SAFEGUARD (The "Barista to Engineer" Rule) 🚨**:
   - Do NOT attempt to force technical keywords (e.g., "Python", "AWS", "microservices") into non-technical past roles (e.g., barista, retail, food service, Uber driver) that the user included to explain a career gap.
   - Leave non-technical experience largely untouched or focus ONLY on transferable soft skills (e.g., leadership, communication, customer service).
   - Any technical keyword injected into a retail or unrelated job will instantly fail the Critic review.

## Output Format
Return the exact JSON structure mapped by the provided output schema.
"""

resume_rewriter_agent = LlmAgent(
    name="ResumeRewriterAgent",
    model=MODEL,
    instruction=INSTRUCTION,
    description="Core rewriting engine: rewrites each resume section without fabricating content.",
    tools=[],
    output_key="resume_rewriter_output",
    output_schema=ResumeRewriterOutputSchema
)
