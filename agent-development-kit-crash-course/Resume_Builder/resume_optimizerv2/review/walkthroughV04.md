# Walkthrough: Fix Resume Text Truncation

## Problem
When running the pipeline via `positive_test_scenario_api.py`, the output HTML resume was missing:
- Contact header (name showed as "UNKNOWN")
- All 8 experience entries
- Education section
- Certifications section

Only the summary and skills survived — everything else was empty.

## Root Cause

A **non-greedy regex** in the JSON extraction utility `get_dict()` / `get_dict_from_state()`:

```python
# BUG: .*? is NON-GREEDY — stops at the first } it finds
re.search(r'```(?:json)?\s*(\{.*?\})\s*```', val, re.DOTALL)
```

The DocumentParser LLM output is a 17,960-char nested JSON wrapped in a markdown code fence. The non-greedy `.*?` matched only the **shortest valid `{...}`** — e.g., `{"completeness_status": "pass"}` — discarding the entire `resume_sections` object with contact, experience, education, etc.

This caused a **cascading failure** through all downstream agents (ResumeRewriter, ATSPrecheck, HTMLRenderer).

## Fix Applied

Changed `.*?` → `.*` (greedy) in **4 files**:

```diff:agent.py
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

def get_dict(val) -> dict:
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict): return val
    if isinstance(val, str):
        import re
        import logging
        logger = logging.getLogger("ResumeRewriter")
        
        # Strategy 1: Try markdown code-block extraction
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', val, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                logger.info(f"✅ get_dict: Extracted JSON from markdown block ({len(match.group(1))} chars)")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ get_dict: Markdown block found but JSON parse failed: {e}")
        
        # Strategy 2: Find the outermost { ... } in the string
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            json_candidate = val[first_brace:last_brace + 1]
            try:
                result = json.loads(json_candidate)
                logger.info(f"✅ get_dict: Extracted JSON via brace matching ({len(json_candidate)} chars)")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ get_dict: Brace matching found but JSON parse failed: {e}")
        
        # Strategy 3: Try parsing the entire string as JSON
        try:
            result = json.loads(val.strip())
            return result
        except json.JSONDecodeError:
            pass
        
        logger.error(f"❌ get_dict: All extraction strategies failed. Input length: {len(val)}, first 200 chars: {val[:200]}")
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
Rewrite the following single experience entry to maximize ATS fit.
Context:
{context}

Original Experience:
{exp}

Rules:
1. Never fabricate dates, titles, or responsibilities.
2. Upgrade weak verbs.
3. Replace special bullet characters with standard hyphens (-).
4. UNRELATED EXPERIENCE SAFEGUARD: Do not force technical keywords into unrelated roles (e.g. barista, retail).
5. PROJECT ENTRY SAFEGUARD: If entry_type is "project", preserve the project framing. Do NOT convert a project description into a job-role format. Keep the project title and description intact.
6. Preserve the entry_type field exactly as provided in the original.
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
    
    # Cross-check against parser's declared experience count to catch upstream truncation
    expected = doc_out.get("experience_entry_count", len(orig_exp))
    assert len(orig_exp) == expected, (
        f"Parser truncation detected! Parser claimed {expected} entries "
        f"but only {len(orig_exp)} were found in the experience array."
    )
    
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
===
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

def get_dict(val) -> dict:
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict): return val
    if isinstance(val, str):
        import re
        import logging
        logger = logging.getLogger("ResumeRewriter")
        
        # Strategy 1: Try markdown code-block extraction
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', val, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                logger.info(f"✅ get_dict: Extracted JSON from markdown block ({len(match.group(1))} chars)")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ get_dict: Markdown block found but JSON parse failed: {e}")
        
        # Strategy 2: Find the outermost { ... } in the string
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            json_candidate = val[first_brace:last_brace + 1]
            try:
                result = json.loads(json_candidate)
                logger.info(f"✅ get_dict: Extracted JSON via brace matching ({len(json_candidate)} chars)")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ get_dict: Brace matching found but JSON parse failed: {e}")
        
        # Strategy 3: Try parsing the entire string as JSON
        try:
            result = json.loads(val.strip())
            return result
        except json.JSONDecodeError:
            pass
        
        logger.error(f"❌ get_dict: All extraction strategies failed. Input length: {len(val)}, first 200 chars: {val[:200]}")
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
Rewrite the following single experience entry to maximize ATS fit.
Context:
{context}

Original Experience:
{exp}

Rules:
1. Never fabricate dates, titles, or responsibilities.
2. Upgrade weak verbs.
3. Replace special bullet characters with standard hyphens (-).
4. UNRELATED EXPERIENCE SAFEGUARD: Do not force technical keywords into unrelated roles (e.g. barista, retail).
5. PROJECT ENTRY SAFEGUARD: If entry_type is "project", preserve the project framing. Do NOT convert a project description into a job-role format. Keep the project title and description intact.
6. Preserve the entry_type field exactly as provided in the original.
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
    
    # Cross-check against parser's declared experience count to catch upstream truncation
    expected = doc_out.get("experience_entry_count", len(orig_exp))
    assert len(orig_exp) == expected, (
        f"Parser truncation detected! Parser claimed {expected} entries "
        f"but only {len(orig_exp)} were found in the experience array."
    )
    
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
```

```diff:agent.py
"""
ATS Pre-Check Agent (Agent 4 of 9) - Deterministic

Detects ATS-unfriendly formatting issues and calculates the
BEFORE ATS keyword match score as a baseline.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from .tools import detect_ats_unfriendly_formatting, calculate_ats_score

def get_dict_from_state(val):
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        import re
        # Strategy 1: markdown code-block extraction
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', val, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        # Strategy 2: outermost brace matching
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(val[first_brace:last_brace + 1])
            except Exception:
                pass
        # Strategy 3: raw string
        try:
            return json.loads(val.strip())
        except Exception:
            pass
    return {}

def run_ats_precheck(state: dict) -> dict:
    doc_out = get_dict_from_state(state.get("document_parser_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))
    
    raw_text = doc_out.get("raw_text", "")
    keywords = jd_out.get("top_keywords", [])
    jd_keywords_csv = ",".join(keywords)

    formatting_check = detect_ats_unfriendly_formatting(raw_text)
    score_result = calculate_ats_score(raw_text, jd_keywords_csv)

    return {
        "formatting_check": formatting_check,
        "ats_score_before": score_result.get("score", 0),
        "matched_keywords_before": score_result.get("matched_keywords", []),
        "missing_keywords": score_result.get("missing_keywords", []),
        "total_jd_keywords": score_result.get("total_jd_keywords", 0)
    }

ats_precheck_agent = PythonTaskNode(
    name="ATSPreCheckAgent",
    task_func=run_ats_precheck,
    output_key="ats_precheck_output",
    description="Deterministic node that detects ATS-unfriendly formatting and calculates BEFORE keyword score."
)
===
"""
ATS Pre-Check Agent (Agent 4 of 9) - Deterministic

Detects ATS-unfriendly formatting issues and calculates the
BEFORE ATS keyword match score as a baseline.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from .tools import detect_ats_unfriendly_formatting, calculate_ats_score

def get_dict_from_state(val):
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        import re
        # Strategy 1: markdown code-block extraction
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', val, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        # Strategy 2: outermost brace matching
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(val[first_brace:last_brace + 1])
            except Exception:
                pass
        # Strategy 3: raw string
        try:
            return json.loads(val.strip())
        except Exception:
            pass
    return {}

def run_ats_precheck(state: dict) -> dict:
    doc_out = get_dict_from_state(state.get("document_parser_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))
    
    raw_text = doc_out.get("raw_text", "")
    keywords = jd_out.get("top_keywords", [])
    jd_keywords_csv = ",".join(keywords)

    formatting_check = detect_ats_unfriendly_formatting(raw_text)
    score_result = calculate_ats_score(raw_text, jd_keywords_csv)

    return {
        "formatting_check": formatting_check,
        "ats_score_before": score_result.get("score", 0),
        "matched_keywords_before": score_result.get("matched_keywords", []),
        "missing_keywords": score_result.get("missing_keywords", []),
        "total_jd_keywords": score_result.get("total_jd_keywords", 0)
    }

ats_precheck_agent = PythonTaskNode(
    name="ATSPreCheckAgent",
    task_func=run_ats_precheck,
    output_key="ats_precheck_output",
    description="Deterministic node that detects ATS-unfriendly formatting and calculates BEFORE keyword score."
)
```

```diff:agent.py
"""
HTML Renderer Agent (Agent 8 of 9) - Deterministic

Converts the rewritten resume JSON into a styled, self-contained
HTML document using Jinja2 templating.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from .tools import render_resume_html

def get_dict_from_state(val):
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        import re
        # Strategy 1: markdown code-block extraction
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', val, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        # Strategy 2: outermost brace matching
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(val[first_brace:last_brace + 1])
            except Exception:
                pass
        # Strategy 3: raw string
        try:
            return json.loads(val.strip())
        except Exception:
            pass
    return {}

def run_html_renderer(state: dict) -> str:
    rewriter_out = get_dict_from_state(state.get("resume_rewriter_output", {}))
    rewritten_resume = rewriter_out.get("rewritten_resume", {})
    
    # Ensure all expected fields are present with empty defaults
    if not isinstance(rewritten_resume.get("contact"), dict):
        rewritten_resume["contact"] = { "name": "", "email": "", "phone": "", "location": "", "linkedin": "" }
    rewritten_resume.setdefault("summary", "")
    rewritten_resume.setdefault("skills", [])
    rewritten_resume.setdefault("experience", [])
    rewritten_resume.setdefault("education", [])
    rewritten_resume.setdefault("certifications", [])

    # The tool expects a JSON string
    rewritten_json = json.dumps(rewritten_resume)
    
    result = render_resume_html(rewritten_json)
    if not result.get("success"):
        raise RuntimeError(f"HTML Rendering Failed: {result.get('error')}")
    
    html_output = result.get("html", "")
        
    return html_output

html_renderer_agent = PythonTaskNode(
    name="HTMLRendererAgent",
    task_func=run_html_renderer,
    output_key="html_renderer_output",
    description="Deterministic node that converts rewritten resume to a styled HTML document."
)
===
"""
HTML Renderer Agent (Agent 8 of 9) - Deterministic

Converts the rewritten resume JSON into a styled, self-contained
HTML document using Jinja2 templating.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from .tools import render_resume_html

def get_dict_from_state(val):
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        import re
        # Strategy 1: markdown code-block extraction
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', val, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        # Strategy 2: outermost brace matching
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(val[first_brace:last_brace + 1])
            except Exception:
                pass
        # Strategy 3: raw string
        try:
            return json.loads(val.strip())
        except Exception:
            pass
    return {}

def run_html_renderer(state: dict) -> str:
    rewriter_out = get_dict_from_state(state.get("resume_rewriter_output", {}))
    rewritten_resume = rewriter_out.get("rewritten_resume", {})
    
    # Ensure all expected fields are present with empty defaults
    if not isinstance(rewritten_resume.get("contact"), dict):
        rewritten_resume["contact"] = { "name": "", "email": "", "phone": "", "location": "", "linkedin": "" }
    rewritten_resume.setdefault("summary", "")
    rewritten_resume.setdefault("skills", [])
    rewritten_resume.setdefault("experience", [])
    rewritten_resume.setdefault("education", [])
    rewritten_resume.setdefault("certifications", [])

    # The tool expects a JSON string
    rewritten_json = json.dumps(rewritten_resume)
    
    result = render_resume_html(rewritten_json)
    if not result.get("success"):
        raise RuntimeError(f"HTML Rendering Failed: {result.get('error')}")
    
    html_output = result.get("html", "")
        
    return html_output

html_renderer_agent = PythonTaskNode(
    name="HTMLRendererAgent",
    task_func=run_html_renderer,
    output_key="html_renderer_output",
    description="Deterministic node that converts rewritten resume to a styled HTML document."
)
```

```diff:agent.py
"""
ATS Scorer Agent — AFTER (Agent 6 of 9) - Deterministic

Re-scores the rewritten resume against JD keywords to measure
improvement and calculate the delta from the baseline score.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from .tools import calculate_ats_score_after

def get_dict_from_state(val):
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        import re
        match = re.search(r'```json\s*(.*?)\s*```', val, re.DOTALL)
        if match:
            clean_str = match.group(1)
        else:
            clean_str = val.strip()
        try:
            return json.loads(clean_str)
        except Exception:
            return {}
    return {}

def run_ats_scorer(state: dict) -> dict:
    rewriter_out = get_dict_from_state(state.get("resume_rewriter_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))
    precheck_out = get_dict_from_state(state.get("ats_precheck_output", {}))

    rewritten_resume = rewriter_out.get("rewritten_resume", {})
    
    # Combine text
    combined_parts = []
    combined_parts.append(rewritten_resume.get("summary", ""))
    combined_parts.append(" ".join(rewritten_resume.get("skills", [])))
    
    for exp in rewritten_resume.get("experience", []):
        combined_parts.append(" ".join(exp.get("bullets", [])))
    
    combined_parts.append(" ".join(rewritten_resume.get("certifications", [])))
    
    combined_text = " ".join(combined_parts)
    
    keywords = jd_out.get("top_keywords", [])
    jd_keywords_csv = ",".join(keywords)

    score_result = calculate_ats_score_after(combined_text, jd_keywords_csv)
    
    score_before = precheck_out.get("ats_score_before", 0)
    score_after = score_result.get("score_after", 0)
    delta = score_after - score_before
    delta_str = f"+{delta} points" if delta >= 0 else f"{delta} points"

    return {
        "ats_score_before": score_before,
        "ats_score_after": score_after,
        "score_delta": delta_str,
        "matched_keywords_after": score_result.get("matched_keywords", []),
        "still_missing_keywords": score_result.get("still_missing_keywords", []),
        "total_jd_keywords": score_result.get("total_jd_keywords", 0),
    }

ats_scorer_agent = PythonTaskNode(
    name="ATSScorerAgent",
    task_func=run_ats_scorer,
    output_key="ats_scorer_output",
    description="Deterministic node that re-scores the rewritten resume and calculates ATS score delta."
)
===
"""
ATS Scorer Agent — AFTER (Agent 6 of 9) - Deterministic

Re-scores the rewritten resume against JD keywords to measure
improvement and calculate the delta from the baseline score.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from .tools import calculate_ats_score_after

def get_dict_from_state(val):
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        import re
        # Strategy 1: markdown code-block extraction (GREEDY to capture full nested JSON)
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', val, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        # Strategy 2: outermost brace matching
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(val[first_brace:last_brace + 1])
            except Exception:
                pass
        # Strategy 3: raw string
        try:
            return json.loads(val.strip())
        except Exception:
            pass
    return {}

def run_ats_scorer(state: dict) -> dict:
    rewriter_out = get_dict_from_state(state.get("resume_rewriter_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))
    precheck_out = get_dict_from_state(state.get("ats_precheck_output", {}))

    rewritten_resume = rewriter_out.get("rewritten_resume", {})
    
    # Combine text
    combined_parts = []
    combined_parts.append(rewritten_resume.get("summary", ""))
    combined_parts.append(" ".join(rewritten_resume.get("skills", [])))
    
    for exp in rewritten_resume.get("experience", []):
        combined_parts.append(" ".join(exp.get("bullets", [])))
    
    combined_parts.append(" ".join(rewritten_resume.get("certifications", [])))
    
    combined_text = " ".join(combined_parts)
    
    keywords = jd_out.get("top_keywords", [])
    jd_keywords_csv = ",".join(keywords)

    score_result = calculate_ats_score_after(combined_text, jd_keywords_csv)
    
    score_before = precheck_out.get("ats_score_before", 0)
    score_after = score_result.get("score_after", 0)
    delta = score_after - score_before
    delta_str = f"+{delta} points" if delta >= 0 else f"{delta} points"

    return {
        "ats_score_before": score_before,
        "ats_score_after": score_after,
        "score_delta": delta_str,
        "matched_keywords_after": score_result.get("matched_keywords", []),
        "still_missing_keywords": score_result.get("still_missing_keywords", []),
        "total_jd_keywords": score_result.get("total_jd_keywords", 0),
    }

ats_scorer_agent = PythonTaskNode(
    name="ATSScorerAgent",
    task_func=run_ats_scorer,
    output_key="ats_scorer_output",
    description="Deterministic node that re-scores the rewritten resume and calculates ATS score delta."
)
```

> [!NOTE]
> The ATS scorer also had a **weaker variant** of the extraction function — it lacked the brace-matching and raw-string fallback strategies. I replaced it with the same robust 3-strategy approach used by the other agents.

## Verification
- Grep confirmed **0 remaining instances** of the non-greedy `.*?` pattern in the codebase.
- Re-run `positive_test_scenario_api.py` to confirm the output now contains all sections.
