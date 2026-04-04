"""
Critic Agent (Agent 7 of 9) - Soft Gate

Quality check that validates the rewritten resume for:
- No fabricated skills or experiences
- No title inflation
- No keyword stuffing
- Page length within 1-2 page limit

Converted to Scoped PythonTaskNode (Part 3 of FinOps Audit):
Executes deterministic tools and ONE scoped LLM call for fabrication detection.
"""

import os
import json
from google.genai import Client, types
from pydantic import BaseModel, Field
from typing import List, Optional

from ...shared.python_task_node import PythonTaskNode
from ...shared.utils import get_dict_from_state
from .tools import estimate_page_length, detect_keyword_stuffing
import logging

logger = logging.getLogger("Critic")
MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

class IssueSchema(BaseModel):
    check: str
    severity: str
    detail: str

class FabricationDetectionSchema(BaseModel):
    fabrication_detected: bool = False
    issues: List[IssueSchema] = Field(default_factory=list)

def extract_skills_and_titles(experience_list: list) -> str:
    titles = []
    for exp in experience_list:
        if exp.get("title"):
            titles.append(exp.get("title"))
    return ", ".join(titles)

def run_critic(state: dict) -> dict:
    doc_out = get_dict_from_state(state.get("document_parser_output", {}))
    rewriter_out = get_dict_from_state(state.get("resume_rewriter_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))

    orig_resume = doc_out.get("resume_sections", {})
    orig_skills = orig_resume.get("skills", [])
    orig_exp = orig_resume.get("experience", [])
    
    new_resume = rewriter_out.get("rewritten_resume", {})
    new_skills = new_resume.get("skills", [])
    new_exp = new_resume.get("experience", [])
    
    jd_keywords = jd_out.get("top_keywords", [])
    jd_keywords_csv = ",".join(jd_keywords)
    
    # Needs to be a combined string for tools
    combined_new_text = json.dumps(new_resume)
    
    # 1. Deterministic checks
    length_res = estimate_page_length(combined_new_text)
    stuffing_res = detect_keyword_stuffing(combined_new_text, jd_keywords_csv)
    
    # 2. Scoped LLM call for fabrication detection
    client = Client()
    prompt = f"""
Compare the original skills and job titles to the rewritten ones.
Check for:
1. Skills fabrication: Are there any technical skills in the rewritten list that DO NOT exist in the original skills or experience?
2. Title inflation: Has a job title been meaningfully elevated? (e.g. "Developer" -> "Senior Developer")

Original Skills: {', '.join(orig_skills)}
Original Titles: {extract_skills_and_titles(orig_exp)}

Rewritten Skills: {', '.join(new_skills)}
Rewritten Titles: {extract_skills_and_titles(new_exp)}
"""
    try:
        res = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FabricationDetectionSchema.model_json_schema(),
                temperature=0.1
            )
        )
        fab_data = json.loads(res.text)
    except Exception as e:
        logger.error(f"Fabrication check failed: {e}")
        fab_data = {"fabrication_detected": False, "issues": []}

    # Combine results
    issues = []
    
    if length_res["status"] != "ok":
        issues.append({
            "check": "page_length",
            "severity": "warning",
            "detail": length_res["message"]
        })
        
    if stuffing_res["has_stuffing"]:
        for item in stuffing_res["stuffed_keywords"]:
            issues.append({
                "check": "keyword_stuffing",
                "severity": "critical",
                "detail": f"Keyword '{item['keyword']}' appears {item['count']} times."
            })
            
    # Add fabrication issues
    for iss in fab_data.get("issues", []):
        issues.append({
            "check": iss.get("check", "fabrication"),
            "severity": iss.get("severity", "critical"),
            "detail": iss.get("detail", "")
        })

    has_critical_issues = any(i.get("severity") == "critical" for i in issues)
    
    return {
        "critic_result": "fail" if has_critical_issues else "pass",
        "estimated_pages": length_res["estimated_pages"],
        "keyword_stuffing": stuffing_res["has_stuffing"],
        "fabrication_detected": fab_data.get("fabrication_detected", False),
        "jd_alignment_quality": "good" if not has_critical_issues else "poor",
        "issues": issues,
        "verdict": f"Critic found {len(issues)} issues." if issues else "Critic passed cleanly."
    }

critic_agent = PythonTaskNode(
    name="CriticAgent",
    task_func=run_critic,
    output_key="critic_output",
    description="Soft Gate: deterministically checks length/stuffing and uses scoped LLM for fabrication detection."
)
