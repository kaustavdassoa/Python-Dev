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
from ...shared.utils import get_dict_from_state
from .prompts import BASE_REWRITE_PROMPT, EXPERIENCE_REWRITE_PROMPT

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
    entry_type: str = Field(default="job", description="Type of entry: 'job', 'project', 'volunteer', or 'other'")

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
    entry_type: str = Field(default="job", description="Type of entry: 'job', 'project', 'volunteer', or 'other'")
    
class RewriterSummarySchema(BaseModel):
    changes_summary: List[str] = Field(default_factory=list)
    keywords_injected: List[str] = Field(default_factory=list)

def run_resume_rewriter(state: dict) -> dict:
    # 1. Gather Context
    doc_out = get_dict_from_state(state.get("document_parser_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))
    pre_out = get_dict_from_state(state.get("ats_precheck_output", {}))
    
    orig_resume = doc_out.get("resume_sections", {})
    orig_exp = orig_resume.get("experience", [])
    
    context_str = f"""
JD Title: {jd_out.get('job_title')}
Keywords: {', '.join(jd_out.get('top_keywords', []))}
Missing Keywords to Inject: {', '.join(pre_out.get('missing_keywords', []))}
"""

    client = Client()
    
    # 2. Rewrite Base Info (Summary, Skills ONLY)
    base_prompt = BASE_REWRITE_PROMPT.format(
        context=context_str,
        summary=orig_resume.get('summary', ''),
        skills=json.dumps(orig_resume.get('skills', []))
    )
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
    
    for i, exp in enumerate(orig_exp):
        print(f"      [Rewriter] Processing experience entry {i+1}/{len(orig_exp)}: {exp.get('title', 'Unknown')}...")
        exp_prompt = EXPERIENCE_REWRITE_PROMPT.format(context=context_str, exp=json.dumps(exp))
        try:
            exp_res = client.models.generate_content(
                model=MODEL,
                contents=exp_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SingleExperienceSchema.model_json_schema(),
                    temperature=0.2
                )
            )
            rewritten_experiences.append(json.loads(exp_res.text))
        except Exception as e:
            print(f"      [Rewriter] ⚠️ Failed on entry {i+1}. Fallback to original. Error: {e}")
            rewritten_experiences.append(exp) # Fallback to original
            
    # Guarantee 1-to-1 data retention
    assert len(orig_exp) == len(rewritten_experiences), "Truncation error! Experience count mismatched."
    
    # Cross-check against parser's declared experience count to catch upstream truncation
    expected = doc_out.get("experience_entry_count", len(orig_exp))
    assert len(orig_exp) == expected, (
        f"Parser truncation detected! Parser claimed {expected} entries "
        f"but only {len(orig_exp)} were found in the experience array."
    )
    
    # 4. Final summary of changes (Deterministic)
    changes_summary = []
    
    # Check skills addition
    orig_skills_set = set(s.lower().strip() for s in orig_resume.get("skills", []))
    new_skills_list = base_info.get("skills", [])
    added_skills = []
    for s in new_skills_list:
        if s.lower().strip() not in orig_skills_set:
            added_skills.append(s)
            
    if added_skills:
        changes_summary.append(f"Added {len(added_skills)} skills: {', '.join(added_skills)}")
        
    # Check summary change
    if orig_resume.get("summary", "").strip() != base_info.get("summary", "").strip():
        changes_summary.append("Rewrote professional summary to highlight ATS keywords.")
        
    # Check experience changes
    exp_changes = 0
    for i, exp in enumerate(orig_exp):
        if i < len(rewritten_experiences):
            if exp.get("bullets") != rewritten_experiences[i].get("bullets"):
                exp_changes += 1
    if exp_changes > 0:
        changes_summary.append(f"Enhanced bullet points in {exp_changes} experience entries.")
        
    jd_keywords = set(k.lower().strip() for k in jd_out.get("top_keywords", []))
    keywords_injected = [s for s in added_skills if s.lower().strip() in jd_keywords]

    
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
        "changes_summary": changes_summary,
        "keywords_injected": keywords_injected,
        "keywords_not_injectable": []
    }

resume_rewriter_agent = PythonTaskNode(
    name="ResumeRewriterAgent",
    task_func=run_resume_rewriter,
    output_key="resume_rewriter_output",
    description="Core rewriting engine: chunked map-reduce to rewrite each section without dropping data."
)
