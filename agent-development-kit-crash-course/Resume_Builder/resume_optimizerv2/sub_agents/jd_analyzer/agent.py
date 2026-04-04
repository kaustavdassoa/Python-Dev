"""
JD Analyzer Agent (Agent 2 of 9)

Analyzes the job description to extract keywords, seniority level,
required skills, and validates JD authenticity.

Converted to Hybrid PythonTaskNode (Part 3 of FinOps Audit):
Executes deterministic tools directly, makes one scoped LLM call for extraction.
"""

import os
import json
from google.genai import Client, types
from pydantic import BaseModel, Field
from typing import List

from ...shared.python_task_node import PythonTaskNode
from .tools import (
    check_jd_authenticity,
    extract_seniority_signals,
    extract_job_metadata,
    extract_ats_keywords
)
import logging

logger = logging.getLogger("JDAnalyzer")
MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

class JDExtractionSchema(BaseModel):
    job_title: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    core_responsibilities: List[str] = Field(default_factory=list)

def run_jd_analyzer(state: dict) -> dict:
    jd_text = state.get("raw_jd_text", "")
    if not jd_text:
        logger.warning("No raw_jd_text found in state.")
        return {}

    # 1. Deterministic tool calls
    auth_result = check_jd_authenticity(jd_text)
    seniority_result = extract_seniority_signals(jd_text)
    metadata_result = extract_job_metadata(jd_text)
    
    # Run the keyword extractor
    keywords_dict = extract_ats_keywords(jd_text)
    top_keywords = keywords_dict.get("keywords", [])
    
    # 2. Scoped LLM call for structure extraction
    client = Client()
    prompt = f"""
Extract the following information from the job description below:
- Job Title
- Required Skills
- Preferred Skills
- Top 5 Core Responsibilities

[JOB DESCRIPTION]
{jd_text}
"""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JDExtractionSchema.model_json_schema(),
                temperature=0.1
            )
        )
        llm_data = json.loads(response.text)
    except Exception as e:
        logger.error(f"JD LLM extraction failed: {e}")
        llm_data = {"job_title": "Unknown Title", "required_skills": [], "preferred_skills": [], "core_responsibilities": []}

    # 3. Merge results
    return {
        "authenticity_status": auth_result.get("authenticity_status", "pass"),
        "authenticity_confidence": auth_result.get("authenticity_confidence", 1.0),
        "job_title": llm_data.get("job_title", ""),
        "seniority_level": seniority_result.get("seniority_level", "mid"),
        "level_score": seniority_result.get("level_score", 2),
        "seniority_signals": seniority_result.get("signals", []),
        "required_skills": llm_data.get("required_skills", []),
        "preferred_skills": llm_data.get("preferred_skills", []),
        "top_keywords": top_keywords,
        "core_responsibilities": llm_data.get("core_responsibilities", []),
        "employment_type": metadata_result.get("employment_type", "full-time"),
        "work_model": metadata_result.get("work_model", "on-site")
    }

jd_analyzer_agent = PythonTaskNode(
    name="JDAnalyzerAgent",
    task_func=run_jd_analyzer,
    output_key="jd_analyzer_output",
    description="Hybrid node: deterministic JD analysis + one scoped LLM call for parsing."
)
