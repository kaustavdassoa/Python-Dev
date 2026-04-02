"""
Resume Rewriter Agent (Agent 5 of 9)

The core rewriting engine. Takes the parsed resume structure and
rewrites every section to maximize ATS keyword match and job fit
while preserving original structure and not fabricating experience.
"""

import os
import json
from google.adk.agents import BaseAgent
from google.genai import Client, types
from pydantic import BaseModel, Field
from typing import List, Optional
from ...shared.python_task_node import PythonTaskNode

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

# Schema for Base Info (Everything Except Experience)
class BaseResumeSchema(BaseModel):
    summary: str = ""
    skills: List[str] = Field(default_factory=list)

# Schema for an Individual Experience Item
class SingleExperienceSchema(BaseModel):
    title: str = ""
    company: str = ""
    dates: str = ""
    bullets: List[str] = Field(default_factory=list)
    
class RewriterSummarySchema(BaseModel):
    changes_summary: List[str] = Field(default_factory=list)
    keywords_injected: List[str] = Field(default_factory=list)

def get_dict(val) -> dict:
    if isinstance(val, dict): return val
    if isinstance(val, str):
        import re
        match = re.search(r'```json\s*(.*?)\s*```', val, re.DOTALL)
        try:
            return json.loads(match.group(1) if match else val.strip())
        except Exception:
            pass
    return {}

def run_resume_rewriter(state: dict) -> dict:
    # 1. Gather Context
    doc_out = get_dict(state.get("document_parser_output", {}))
    jd_out = get_dict(state.get("jd_analyzer_output", {}))
    pre_out = get_dict(state.get("ats_precheck_output", {}))
    
    orig_resume = doc_out.get("resume_sections", {})
    orig_exp = orig_resume.get("experience", [])
    
    context_str = f"""
JD Title: {jd_out.get('job_title')}
Keywords: {', '.join(jd_out.get('top_keywords', []))}
Missing Keywords to Inject: {', '.join(pre_out.get('missing_keywords', []))}
"""

    client = Client()
    
    # 2. Rewrite Base Info (Summary, Skills ONLY)
    base_prompt = f"""
Rewrite the summary and skills sections of this resume to maximize ATS fit.
Context:
{context_str}

Original Summary:
{orig_resume.get('summary', '')}

Original Skills:
{json.dumps(orig_resume.get('skills', []))}

Rules:
1. Never fabricate skills not in the original.
2. Natural keyword injection only.
"""
    base_res = client.models.generate_content(
        model=MODEL,
        contents=base_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BaseResumeSchema.model_json_schema(),
            temperature=0.2
        )
    )
    base_info = json.loads(base_res.text)
    
    # 3. Chunked Experience Rewriting (Map-Reduce)
    rewritten_experiences = []
    changes = []
    injected = []
    
    exp_prompt_template = """
Rewrite the following single job experience to maximize ATS fit.
Context:
{context}

Original Experience:
{exp}

Rules:
1. Never fabricate dates, titles, or responsibilities.
2. Upgrade weak verbs.
3. Replace special bullet characters with standard hyphens (-).
4. UNRELATED EXPERIENCE SAFEGUARD: Do not force technical keywords into unrelated roles (e.g. barista, retail).
"""
    
    for exp in orig_exp:
        exp_res = client.models.generate_content(
            model=MODEL,
            contents=exp_prompt_template.format(context=context_str, exp=json.dumps(exp)),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SingleExperienceSchema.model_json_schema(),
                temperature=0.2
            )
        )
        try:
            rewritten_experiences.append(json.loads(exp_res.text))
        except Exception:
            rewritten_experiences.append(exp) # Fallback to original
            
    # Guarantee 1-to-1 data retention
    assert len(orig_exp) == len(rewritten_experiences), "Truncation error! Experience count mismatched."
    
    # 4. Final summary of changes
    summary_res = client.models.generate_content(
        model=MODEL,
        contents="Summarize changes made and keywords successfully injected. Base: " + json.dumps(base_info) + " Exp: " + json.dumps(rewritten_experiences),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RewriterSummarySchema.model_json_schema(),
            temperature=0.2
        )
    )
    summary_info = json.loads(summary_res.text)
    
    # Combine everything
    out_resume = {
        "contact": orig_resume.get("contact", {}),
        "summary": base_info.get("summary", ""),
        "skills": base_info.get("skills", []),
        "education": orig_resume.get("education", []),
        "certifications": orig_resume.get("certifications", []),
        "experience": rewritten_experiences
    }
    
    return {
        "rewritten_resume": out_resume,
        "changes_summary": summary_info.get("changes_summary", []),
        "keywords_injected": summary_info.get("keywords_injected", []),
        "keywords_not_injectable": []
    }

resume_rewriter_agent = PythonTaskNode(
    name="ResumeRewriterAgent",
    task_func=run_resume_rewriter,
    output_key="resume_rewriter_output",
    description="Core rewriting engine: chunked map-reduce to rewrite each section without dropping data."
)
