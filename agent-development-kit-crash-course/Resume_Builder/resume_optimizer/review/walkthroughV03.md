# Walkthrough: Resume Parsing Anti-Truncation Fix

## Problem
Multi-page resumes were dropping older job entries, and sections under non-standard headers like "SELECTED PROJECTS" were silently ignored. Root cause: the DocumentParserAgent's LLM prompt lacked exhaustive extraction directives and header synonym mapping.

## Changes Made

### 1. PDF Parser — Page Boundary Markers
```diff:tools.py
"""
Document Parser Tools

Handles extraction of resume text from PDF, DOCX, and plain text formats.
"""

import os

import io

def parse_pdf(file_bytes: bytes) -> dict:
    """
    Extract text content from a PDF resume.

    Args:
        file_bytes: Bytes containing the PDF data

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    try:
        import pdfplumber
    except ImportError:
        return {
            "success": False,
            "text": "",
            "error": "pdfplumber not installed. Run: pip install pdfplumber",
        }

    if not file_bytes:
        return {"success": False, "text": "", "error": "PDF bytes are empty"}

    try:
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            return {
                "success": False,
                "text": "",
                "error": "PDF appears to be empty or image-only. Try converting to DOCX first.",
            }

        return {"success": True, "text": full_text, "error": None}

    except Exception as e:
        return {"success": False, "text": "", "error": f"PDF parsing failed: {str(e)}"}


def parse_docx(file_bytes: bytes) -> dict:
    """
    Extract text content from a DOCX resume.

    Args:
        file_bytes: Bytes containing the DOCX data

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    try:
        from docx import Document
    except ImportError:
        return {
            "success": False,
            "text": "",
            "error": "python-docx not installed. Run: pip install python-docx",
        }

    if not file_bytes:
        return {"success": False, "text": "", "error": "DOCX bytes are empty"}

    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        full_text = "\n".join(paragraphs).strip()

        if not full_text:
            return {"success": False, "text": "", "error": "DOCX appears to be empty."}

        return {"success": True, "text": full_text, "error": None}

    except Exception as e:
        return {"success": False, "text": "", "error": f"DOCX parsing failed: {str(e)}"}


def parse_plain_text(text: str) -> dict:
    """
    Process plain text resume content (passthrough with cleanup).

    Args:
        text: Raw resume text pasted by the user.

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    if not text or not text.strip():
        return {"success": False, "text": "", "error": "Provided text is empty."}

    cleaned = text.strip()
    return {"success": True, "text": cleaned, "error": None}


def parse_resume_file(file_path: str) -> dict:
    """
    Parse a resume from a local file path. Supports PDF, DOCX, and TXT files.
    Use this tool when the user provides a file path to their resume.

    Args:
        file_path: The full absolute path to the resume file on disk.
                   Example: "E:/Documents/MyResume.pdf"

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    if not file_path or not file_path.strip():
        return {"success": False, "text": "", "error": "No file path provided."}

    file_path = file_path.strip().strip('"').strip("'")

    if not os.path.exists(file_path):
        return {"success": False, "text": "", "error": f"File not found: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        return {"success": False, "text": "", "error": f"Could not read file: {str(e)}"}

    if ext == ".pdf":
        return parse_pdf(file_bytes)
    elif ext == ".docx":
        return parse_docx(file_bytes)
    elif ext == ".txt":
        return parse_plain_text(file_bytes.decode("utf-8", errors="ignore"))
    else:
        return {"success": False, "text": "", "error": f"Unsupported file type: {ext}. Use .pdf, .docx, or .txt"}

===
"""
Document Parser Tools

Handles extraction of resume text from PDF, DOCX, and plain text formats.
"""

import os

import io

def parse_pdf(file_bytes: bytes) -> dict:
    """
    Extract text content from a PDF resume.

    Args:
        file_bytes: Bytes containing the PDF data

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    try:
        import pdfplumber
    except ImportError:
        return {
            "success": False,
            "text": "",
            "error": "pdfplumber not installed. Run: pip install pdfplumber",
        }

    if not file_bytes:
        return {"success": False, "text": "", "error": "PDF bytes are empty"}

    try:
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    # Inject page-boundary markers for multi-page resumes
                    if total_pages > 1 and i < total_pages - 1:
                        text_parts.append(f"\n--- PAGE {i+1} OF {total_pages} ---\n")

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            return {
                "success": False,
                "text": "",
                "error": "PDF appears to be empty or image-only. Try converting to DOCX first.",
            }

        return {"success": True, "text": full_text, "error": None}

    except Exception as e:
        return {"success": False, "text": "", "error": f"PDF parsing failed: {str(e)}"}


def parse_docx(file_bytes: bytes) -> dict:
    """
    Extract text content from a DOCX resume.

    Args:
        file_bytes: Bytes containing the DOCX data

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    try:
        from docx import Document
    except ImportError:
        return {
            "success": False,
            "text": "",
            "error": "python-docx not installed. Run: pip install python-docx",
        }

    if not file_bytes:
        return {"success": False, "text": "", "error": "DOCX bytes are empty"}

    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        full_text = "\n".join(paragraphs).strip()

        if not full_text:
            return {"success": False, "text": "", "error": "DOCX appears to be empty."}

        return {"success": True, "text": full_text, "error": None}

    except Exception as e:
        return {"success": False, "text": "", "error": f"DOCX parsing failed: {str(e)}"}


def parse_plain_text(text: str) -> dict:
    """
    Process plain text resume content (passthrough with cleanup).

    Args:
        text: Raw resume text pasted by the user.

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    if not text or not text.strip():
        return {"success": False, "text": "", "error": "Provided text is empty."}

    cleaned = text.strip()
    return {"success": True, "text": cleaned, "error": None}


def parse_resume_file(file_path: str) -> dict:
    """
    Parse a resume from a local file path. Supports PDF, DOCX, and TXT files.
    Use this tool when the user provides a file path to their resume.

    Args:
        file_path: The full absolute path to the resume file on disk.
                   Example: "E:/Documents/MyResume.pdf"

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    if not file_path or not file_path.strip():
        return {"success": False, "text": "", "error": "No file path provided."}

    file_path = file_path.strip().strip('"').strip("'")

    if not os.path.exists(file_path):
        return {"success": False, "text": "", "error": f"File not found: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        return {"success": False, "text": "", "error": f"Could not read file: {str(e)}"}

    if ext == ".pdf":
        return parse_pdf(file_bytes)
    elif ext == ".docx":
        return parse_docx(file_bytes)
    elif ext == ".txt":
        return parse_plain_text(file_bytes.decode("utf-8", errors="ignore"))
    else:
        return {"success": False, "text": "", "error": f"Unsupported file type: {ext}. Use .pdf, .docx, or .txt"}

```

`parse_pdf()` now injects `--- PAGE X OF Y ---` markers between pages, giving the LLM an unambiguous signal that content continues.

---

### 2. DocumentParserAgent — RSCIT Prompt Rewrite
```diff:agent.py
"""
Document Parser Agent (Agent 1 of 9)

Parses the user's resume from PDF, DOCX, or plain text.
Checks resume completeness before allowing the pipeline to proceed.
"""

import os
from google.adk.agents import LlmAgent
from .tools import parse_resume_file

MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

INSTRUCTION = """
You are the **Document Parser Agent** — the first step in the Resume Optimizer Pipeline.

## Your Mission
Parse the user's resume and check that it contains the minimum required sections.

## How To Get The Resume Text
There are two ways the resume text can reach you:

1. **Pre-parsed text in state**: If the session state contains a field called raw_resume_text,
   use that text directly. This happens when the FastAPI server pre-parses the uploaded file.

2. **File path from user**: If the user provides a local file path (e.g., ending in .pdf, .docx, or .txt),
   call the parse_resume_file tool with that path to extract the text.

3. **Pasted text from user**: If the user pastes resume text directly in the chat,
   use that text as-is.

## Step 1: Identify and Label Resume Sections
From the resume text (obtained above), identify and structure these sections:
- **contact**: Full name, email, phone, LinkedIn URL, location/city
- **summary**: Professional summary, objective, or profile statement
- **experience**: List of jobs — each with company, job title, dates, bullet points
- **skills**: Technical skills, tools, programming languages, frameworks
- **education**: Degrees, institutions, graduation years
- **certifications**: Professional certifications (may be absent — that's OK)

Preserve the ORIGINAL order of sections as they appear in the resume.

## Step 2: Completeness Check
**Required sections:** contact, experience, skills
If ANY required section is missing or empty:
- Set completeness_status to "fail"
- List the missing sections

If all required sections are present:
- Set completeness_status to "pass"

## Output Format
Output a **single JSON block** with this exact structure:
```json
{
  "completeness_status": "pass",
  "missing_sections": [],
  "resume_sections": {
    "contact": {
      "name": "...",
      "email": "...",
      "phone": "...",
      "location": "...",
      "linkedin": "..."
    },
    "summary": "...",
    "skills": ["...", "..."],
    "experience": [
      {
        "title": "...",
        "company": "...",
        "dates": "...",
        "bullets": ["...", "..."]
      }
    ],
    "education": [
      {
        "degree": "...",
        "institution": "...",
        "year": "..."
      }
    ],
    "certifications": []
  },
  "raw_text": "full extracted resume text here"
}
```

## If Completeness FAILS
After the JSON, add on a new line:
❌ PIPELINE HALTED: Resume is missing required sections: [list them]. Please add these sections and try again.

## If Completeness PASSES
After the JSON, add on a new line:
✅ Resume parsed successfully. Proceeding to JD analysis.
"""

document_parser_agent = LlmAgent(
    name="DocumentParserAgent",
    model=MODEL,
    instruction=INSTRUCTION,
    description="Parses resume text from state or file path and checks completeness.",
    tools=[parse_resume_file],
    output_key="document_parser_output",
)
===
"""
Document Parser Agent (Agent 1 of 9)

Parses the user's resume from PDF, DOCX, or plain text.
Checks resume completeness before allowing the pipeline to proceed.
"""

import os
from google.adk.agents import LlmAgent
from .tools import parse_resume_file

MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

INSTRUCTION = """
You are the **Document Parser Agent** — the first step in the Resume Optimizer Pipeline.

## Your Mission
Parse the user's resume and extract EVERY section into structured JSON. Check that it
contains the minimum required sections before proceeding.

## How To Get The Resume Text
There are two ways the resume text can reach you:

1. **Pre-parsed text in state**: If the session state contains a field called raw_resume_text,
   use that text directly. This happens when the FastAPI server pre-parses the uploaded file.

2. **File path from user**: If the user provides a local file path (e.g., ending in .pdf, .docx, or .txt),
   call the parse_resume_file tool with that path to extract the text.

3. **Pasted text from user**: If the user pastes resume text directly in the chat,
   use that text as-is.

## CRITICAL ANTI-TRUNCATION RULE
Resumes may span multiple pages. Page boundaries are marked with `--- PAGE X OF Y ---`.
You MUST extract EVERY role, position, project, and employment entry from the ENTIRE resume,
including content from ALL pages. Do NOT stop after the first page.

Count the total number of distinct job/role/project entries you find in the raw text, then
verify your output contains exactly that many objects in the experience array. If your output
has fewer entries than the source text, your extraction has FAILED — go back and add the
missing entries.

## Section Header Synonym Map
Resumes use many header variations. Map ALL of these to the corresponding canonical section:

| Canonical Section | Accepted Headers (case-insensitive) |
|---|---|
| experience | "Work Experience", "Professional Experience", "Employment History", "Career History", "Relevant Experience", "Work History" |
| experience | "SELECTED PROJECTS", "Key Projects", "Project Experience", "Projects", "Consulting Engagements", "Freelance Work", "Contract Work", "Volunteer Experience", "Leadership Experience" |
| skills | "Technical Skills", "Core Competencies", "Areas of Expertise", "Proficiencies", "Technologies", "Tools & Technologies", "Tech Stack" |
| education | "Education", "Academic Background", "Qualifications", "Training", "Academic Credentials" |
| certifications | "Certifications", "Licenses", "Professional Development", "Credentials", "Certificates" |
| summary | "Summary", "Profile", "Objective", "Professional Summary", "Executive Summary", "About Me", "Career Objective" |
| contact | "Contact", "Contact Information", "Personal Information" |

ANY section header NOT in this table should still be extracted — place it in the closest
matching canonical section. If no match is found, include it as an additional entry in the
experience array with entry_type: "other".

## Step 1: Identify and Label Resume Sections
From the resume text (obtained above), identify and structure these sections:
- **contact**: Full name, email, phone, LinkedIn URL, location/city
- **summary**: Professional summary, objective, or profile statement
- **experience**: List of ALL jobs, projects, and other entries — each with company, job title, dates, bullet points, and entry_type
- **skills**: Technical skills, tools, programming languages, frameworks
- **education**: Degrees, institutions, graduation years
- **certifications**: Professional certifications (may be absent — that's OK)

Preserve the ORIGINAL order of sections as they appear in the resume.

## Step 2: Assign entry_type to Each Experience Entry
For each entry in the experience array, assign one of these types:
- "job" — standard employment (has company, title, dates)
- "project" — selected projects, key projects, consulting engagements
- "volunteer" — volunteer or community work
- "other" — anything that doesn't fit the above categories

## Step 3: Self-Verification (Chain-of-Thought)
Before generating your final JSON, perform this internal check:
1. Count the number of distinct job/role/project headers in the raw text.
2. Count the number of objects in your experience array.
3. If count 1 ≠ count 2, you have truncated data. Go back and add the missing entries.
4. Set experience_entry_count to the final count.

## Step 4: Completeness Check
**Required sections:** contact, experience, skills
If ANY required section is missing or empty:
- Set completeness_status to "fail"
- List the missing sections

If all required sections are present:
- Set completeness_status to "pass"

## Output Format
Output a **single JSON block** with this exact structure:
```json
{
  "completeness_status": "pass",
  "missing_sections": [],
  "experience_entry_count": 5,
  "resume_sections": {
    "contact": {
      "name": "...",
      "email": "...",
      "phone": "...",
      "location": "...",
      "linkedin": "..."
    },
    "summary": "...",
    "skills": ["...", "..."],
    "experience": [
      {
        "title": "...",
        "company": "...",
        "dates": "...",
        "bullets": ["...", "..."],
        "entry_type": "job"
      },
      {
        "title": "...",
        "company": "...",
        "dates": "...",
        "bullets": ["...", "..."],
        "entry_type": "project"
      }
    ],
    "education": [
      {
        "degree": "...",
        "institution": "...",
        "year": "..."
      }
    ],
    "certifications": []
  },
  "raw_text": "full extracted resume text here"
}
```

## If Completeness FAILS
After the JSON, add on a new line:
❌ PIPELINE HALTED: Resume is missing required sections: [list them]. Please add these sections and try again.

## If Completeness PASSES
After the JSON, add on a new line:
✅ Resume parsed successfully. Proceeding to JD analysis.
"""

document_parser_agent = LlmAgent(
    name="DocumentParserAgent",
    model=MODEL,
    instruction=INSTRUCTION,
    description="Parses resume text from state or file path and checks completeness.",
    tools=[parse_resume_file],
    output_key="document_parser_output",
)
```

The instruction was rewritten using the RSCIT framework with:
- **Anti-Truncation Rule** — explicit directive to extract every entry from all pages
- **Header Synonym Map** — maps 30+ common resume header variants to canonical sections
- **entry_type discriminator** — classifies each experience entry as `job`, `project`, `volunteer`, or `other`
- **Self-Verification step** — chain-of-thought count check before output
- **experience_entry_count** — new field for downstream cross-checking

---

### 3. State Schema Documentation
```diff:state.py
"""
Shared session state schema for the Resume Optimizer pipeline.

All agents read from and write to ADK session state using these constants.
The state is passed in-memory through the SequentialAgent pipeline.
"""

# ── Stage 1: Document Parser ──────────────────────────────────────────────────
DOCUMENT_PARSER_OUTPUT = "document_parser_output"
# JSON: { completeness_status, missing_sections, resume_sections, raw_text }

# ── Stage 2: JD Analyzer ─────────────────────────────────────────────────────
JD_ANALYZER_OUTPUT = "jd_analyzer_output"
# JSON: { authenticity_status, job_title, seniority_level, required_skills,
#         preferred_skills, top_keywords, responsibilities, employment_type }

# ── Stage 3: Alignment Validator ─────────────────────────────────────────────
ALIGNMENT_VALIDATOR_OUTPUT = "alignment_validator_output"
# JSON: { alignment_result, candidate_level, jd_level, seniority_gap,
#         domain_overlap_pct, rejection_message }

# ── Stage 4: ATS Pre-Check ───────────────────────────────────────────────────
ATS_PRECHECK_OUTPUT = "ats_precheck_output"
# JSON: { formatting_warnings, ats_score_before, matched_keywords_before,
#         missing_keywords }

# ── Stage 5: Resume Rewriter ─────────────────────────────────────────────────
RESUME_REWRITER_OUTPUT = "resume_rewriter_output"
# JSON: { rewritten_resume: { contact, summary, skills, experience, education,
#         certifications }, changes_summary }

# ── Stage 6: ATS Scorer (After) ──────────────────────────────────────────────
ATS_SCORER_OUTPUT = "ats_scorer_output"
# JSON: { ats_score_after, score_delta, still_missing_keywords,
#         matched_keywords_after }

# ── Stage 7: Critic ──────────────────────────────────────────────────────────
CRITIC_OUTPUT = "critic_output"
# JSON: { critic_result, issues, estimated_pages }

# ── Stage 8: HTML Renderer ───────────────────────────────────────────────────
HTML_RENDERER_OUTPUT = "html_renderer_output"
# String: complete self-contained HTML document

# ── Stage 9: Report Generator ────────────────────────────────────────────────
FINAL_REPORT = "final_report"
# String: formatted analysis report (markdown / plain text)

# ── Pipeline Control Signals ─────────────────────────────────────────────────
PIPELINE_HALTED = "pipeline_halted"
HALT_REASON = "halt_reason"
===
"""
Shared session state schema for the Resume Optimizer pipeline.

All agents read from and write to ADK session state using these constants.
The state is passed in-memory through the SequentialAgent pipeline.
"""

# ── Stage 1: Document Parser ──────────────────────────────────────────────────
DOCUMENT_PARSER_OUTPUT = "document_parser_output"
# JSON: { completeness_status, missing_sections, experience_entry_count,
#         resume_sections: { contact, summary, skills,
#             experience: [{ title, company, dates, bullets, entry_type }],
#             education, certifications },
#         raw_text }
# entry_type values: "job", "project", "volunteer", "other"

# ── Stage 2: JD Analyzer ─────────────────────────────────────────────────────
JD_ANALYZER_OUTPUT = "jd_analyzer_output"
# JSON: { authenticity_status, job_title, seniority_level, required_skills,
#         preferred_skills, top_keywords, responsibilities, employment_type }

# ── Stage 3: Alignment Validator ─────────────────────────────────────────────
ALIGNMENT_VALIDATOR_OUTPUT = "alignment_validator_output"
# JSON: { alignment_result, candidate_level, jd_level, seniority_gap,
#         domain_overlap_pct, rejection_message }

# ── Stage 4: ATS Pre-Check ───────────────────────────────────────────────────
ATS_PRECHECK_OUTPUT = "ats_precheck_output"
# JSON: { formatting_warnings, ats_score_before, matched_keywords_before,
#         missing_keywords }

# ── Stage 5: Resume Rewriter ─────────────────────────────────────────────────
RESUME_REWRITER_OUTPUT = "resume_rewriter_output"
# JSON: { rewritten_resume: { contact, summary, skills, experience, education,
#         certifications }, changes_summary }

# ── Stage 6: ATS Scorer (After) ──────────────────────────────────────────────
ATS_SCORER_OUTPUT = "ats_scorer_output"
# JSON: { ats_score_after, score_delta, still_missing_keywords,
#         matched_keywords_after }

# ── Stage 7: Critic ──────────────────────────────────────────────────────────
CRITIC_OUTPUT = "critic_output"
# JSON: { critic_result, issues, estimated_pages }

# ── Stage 8: HTML Renderer ───────────────────────────────────────────────────
HTML_RENDERER_OUTPUT = "html_renderer_output"
# String: complete self-contained HTML document

# ── Stage 9: Report Generator ────────────────────────────────────────────────
FINAL_REPORT = "final_report"
# String: formatted analysis report (markdown / plain text)

# ── Pipeline Control Signals ─────────────────────────────────────────────────
PIPELINE_HALTED = "pipeline_halted"
HALT_REASON = "halt_reason"
```

Updated `DOCUMENT_PARSER_OUTPUT` contract to reflect new fields.

---

### 4. Resume Rewriter — Schema + Prompt + Assertion
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

- Added `entry_type` field to `ExperienceSchema` and `SingleExperienceSchema`
- Added **PROJECT ENTRY SAFEGUARD** to the rewriting prompt
- Added runtime assertion cross-checking `experience_entry_count` from parser

---

### 5. Jinja2 Template — Entry-Type Rendering
```diff:resume.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ contact.name if contact else "Resume" }} — Resume</title>
  <style>
    /* ── Reset ─────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    /* ── Page ───────────────────────────────────────────── */
    body {
      font-family: 'Georgia', 'Times New Roman', serif;
      font-size: 10.5pt;
      color: #1a1a2e;
      background: #f0f2f5;
      padding: 30px 20px;
      line-height: 1.5;
    }

    .resume-wrapper {
      max-width: 820px;
      margin: 0 auto;
      background: #ffffff;
      padding: 44px 56px;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0,0,0,0.05);
      border-radius: 4px;
    }

    /* ── Header / Contact ───────────────────────────────── */
    .header {
      text-align: center;
      padding-bottom: 18px;
      margin-bottom: 22px;
      border-bottom: 2.5px solid #1a365d;
    }

    .candidate-name {
      font-size: 24pt;
      font-weight: bold;
      color: #1a365d;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    .contact-bar {
      font-size: 9.5pt;
      color: #555;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 4px 16px;
    }

    .contact-bar a {
      color: #1a365d;
      text-decoration: none;
    }

    .contact-bar a:hover { text-decoration: underline; }

    .contact-sep { color: #bbb; }

    /* ── Sections ───────────────────────────────────────── */
    .section {
      margin-bottom: 20px;
    }

    .section-title {
      font-size: 9.5pt;
      font-weight: bold;
      color: #1a365d;
      text-transform: uppercase;
      letter-spacing: 2px;
      border-bottom: 1.5px solid #1a365d;
      padding-bottom: 4px;
      margin-bottom: 10px;
      font-family: 'Arial', sans-serif;
    }

    /* ── Summary ────────────────────────────────────────── */
    .summary-text {
      font-size: 10pt;
      color: #363636;
      line-height: 1.65;
    }

    /* ── Skills ─────────────────────────────────────────── */
    .skills-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      list-style: none;
    }

    .skill-tag {
      background: #eef2f8;
      color: #1a365d;
      border: 1px solid #c5d3e8;
      padding: 3px 11px;
      border-radius: 3px;
      font-size: 9pt;
      font-family: 'Arial', sans-serif;
      font-weight: 500;
    }

    /* ── Experience ─────────────────────────────────────── */
    .job {
      margin-bottom: 14px;
    }

    .job-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 4px;
    }

    .job-title-company {
      font-size: 10.5pt;
    }

    .job-title {
      font-weight: bold;
      color: #1a1a2e;
    }

    .job-company {
      font-style: italic;
      color: #4a4a6a;
    }

    .job-dates {
      font-size: 9.5pt;
      color: #666;
      white-space: nowrap;
      font-family: 'Arial', sans-serif;
    }

    .job-bullets {
      margin-top: 5px;
      padding-left: 20px;
      list-style-type: disc;
    }

    .job-bullets li {
      font-size: 10pt;
      color: #333;
      margin-bottom: 3px;
      line-height: 1.6;
    }

    /* ── Education ──────────────────────────────────────── */
    .edu-item {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 8px;
      flex-wrap: wrap;
      gap: 4px;
    }

    .edu-degree {
      font-weight: bold;
      font-size: 10.5pt;
      color: #1a1a2e;
    }

    .edu-institution {
      font-style: italic;
      font-size: 10pt;
      color: #4a4a6a;
    }

    .edu-year {
      font-size: 9.5pt;
      color: #666;
      white-space: nowrap;
      font-family: 'Arial', sans-serif;
    }

    /* ── Certifications ─────────────────────────────────── */
    .cert-list {
      list-style-type: disc;
      padding-left: 20px;
    }

    .cert-list li {
      font-size: 10pt;
      color: #333;
      line-height: 1.6;
      margin-bottom: 2px;
    }

    /* ── Print ──────────────────────────────────────────── */
    @media print {
      body, html { 
        background: white; 
        padding: 0; 
        margin: 0;
        font-size: 10pt; 
        height: auto !important; 
        overflow: visible !important;
      }
      .resume-wrapper { 
        box-shadow: none; 
        padding: 0; 
        margin: 0; 
        border-radius: 0; 
        max-width: none; 
        width: 100%;
      }
      .section { 
        page-break-inside: auto; 
      }
      .job { 
        page-break-inside: avoid; 
      }
      .edu-item { 
        page-break-inside: avoid; 
      }
      .cert-list {
        page-break-inside: auto;
      }
    }
  </style>
</head>
<body>
  <div class="resume-wrapper">

    <!-- ── Contact Header ────────────────────────────────── -->
    {% if contact %}
    <div class="header">
      {% if contact.name %}
      <div class="candidate-name">{{ contact.name }}</div>
      {% endif %}
      <div class="contact-bar">
        {% if contact.email %}
        <a href="mailto:{{ contact.email }}">{{ contact.email }}</a>
        {% endif %}
        {% if contact.phone %}
        <span class="contact-sep">|</span>
        <span>{{ contact.phone }}</span>
        {% endif %}
        {% if contact.location %}
        <span class="contact-sep">|</span>
        <span>{{ contact.location }}</span>
        {% endif %}
        {% if contact.linkedin %}
        <span class="contact-sep">|</span>
        <a href="{{ contact.linkedin }}" target="_blank">{{ contact.linkedin }}</a>
        {% endif %}
      </div>
    </div>
    {% endif %}

    <!-- ── Professional Summary ──────────────────────────── -->
    {% if summary %}
    <div class="section">
      <div class="section-title">Professional Summary</div>
      <p class="summary-text">{{ summary }}</p>
    </div>
    {% endif %}

    <!-- ── Skills ───────────────────────────────────────── -->
    {% if skills %}
    <div class="section">
      <div class="section-title">Technical Skills</div>
      <ul class="skills-grid">
        {% for skill in skills %}
        <li class="skill-tag">{{ skill }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    <!-- ── Professional Experience ──────────────────────── -->
    {% if experience %}
    <div class="section">
      <div class="section-title">Professional Experience</div>
      {% for job in experience %}
      <div class="job">
        <div class="job-header">
          <div class="job-title-company">
            <span class="job-title">{{ job.title | default('') }}</span>
            {% if job.company %}
            &nbsp;&mdash;&nbsp;<span class="job-company">{{ job.company }}</span>
            {% endif %}
          </div>
          {% if job.dates %}
          <span class="job-dates">{{ job.dates }}</span>
          {% endif %}
        </div>
        {% if job.bullets %}
        <ul class="job-bullets">
          {% for bullet in job.bullets %}
          <li>{{ bullet }}</li>
          {% endfor %}
        </ul>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- ── Education ────────────────────────────────────── -->
    {% if education %}
    <div class="section">
      <div class="section-title">Education</div>
      {% for edu in education %}
      <div class="edu-item">
        <div>
          <div class="edu-degree">{{ edu.degree | default('') }}</div>
          {% if edu.institution %}
          <div class="edu-institution">{{ edu.institution }}</div>
          {% endif %}
        </div>
        {% if edu.year %}
        <span class="edu-year">{{ edu.year }}</span>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- ── Certifications ───────────────────────────────── -->
    {% if certifications and certifications | length > 0 %}
    <div class="section">
      <div class="section-title">Certifications</div>
      <ul class="cert-list">
        {% for cert in certifications %}
        <li>{{ cert }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

  </div><!-- /.resume-wrapper -->
</body>
</html>
===
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ contact.name if contact else "Resume" }} — Resume</title>
  <style>
    /* ── Reset ─────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    /* ── Page ───────────────────────────────────────────── */
    body {
      font-family: 'Georgia', 'Times New Roman', serif;
      font-size: 10.5pt;
      color: #1a1a2e;
      background: #f0f2f5;
      padding: 30px 20px;
      line-height: 1.5;
    }

    .resume-wrapper {
      max-width: 820px;
      margin: 0 auto;
      background: #ffffff;
      padding: 44px 56px;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0,0,0,0.05);
      border-radius: 4px;
    }

    /* ── Header / Contact ───────────────────────────────── */
    .header {
      text-align: center;
      padding-bottom: 18px;
      margin-bottom: 22px;
      border-bottom: 2.5px solid #1a365d;
    }

    .candidate-name {
      font-size: 24pt;
      font-weight: bold;
      color: #1a365d;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    .contact-bar {
      font-size: 9.5pt;
      color: #555;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 4px 16px;
    }

    .contact-bar a {
      color: #1a365d;
      text-decoration: none;
    }

    .contact-bar a:hover { text-decoration: underline; }

    .contact-sep { color: #bbb; }

    /* ── Sections ───────────────────────────────────────── */
    .section {
      margin-bottom: 20px;
    }

    .section-title {
      font-size: 9.5pt;
      font-weight: bold;
      color: #1a365d;
      text-transform: uppercase;
      letter-spacing: 2px;
      border-bottom: 1.5px solid #1a365d;
      padding-bottom: 4px;
      margin-bottom: 10px;
      font-family: 'Arial', sans-serif;
    }

    /* ── Summary ────────────────────────────────────────── */
    .summary-text {
      font-size: 10pt;
      color: #363636;
      line-height: 1.65;
    }

    /* ── Skills ─────────────────────────────────────────── */
    .skills-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      list-style: none;
    }

    .skill-tag {
      background: #eef2f8;
      color: #1a365d;
      border: 1px solid #c5d3e8;
      padding: 3px 11px;
      border-radius: 3px;
      font-size: 9pt;
      font-family: 'Arial', sans-serif;
      font-weight: 500;
    }

    /* ── Experience ─────────────────────────────────────── */
    .job {
      margin-bottom: 14px;
    }

    .job-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 4px;
    }

    .job-title-company {
      font-size: 10.5pt;
    }

    .job-title {
      font-weight: bold;
      color: #1a1a2e;
    }

    .job-company {
      font-style: italic;
      color: #4a4a6a;
    }

    .job-dates {
      font-size: 9.5pt;
      color: #666;
      white-space: nowrap;
      font-family: 'Arial', sans-serif;
    }

    .job-bullets {
      margin-top: 5px;
      padding-left: 20px;
      list-style-type: disc;
    }

    .job-bullets li {
      font-size: 10pt;
      color: #333;
      margin-bottom: 3px;
      line-height: 1.6;
    }

    /* ── Education ──────────────────────────────────────── */
    .edu-item {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 8px;
      flex-wrap: wrap;
      gap: 4px;
    }

    .edu-degree {
      font-weight: bold;
      font-size: 10.5pt;
      color: #1a1a2e;
    }

    .edu-institution {
      font-style: italic;
      font-size: 10pt;
      color: #4a4a6a;
    }

    .edu-year {
      font-size: 9.5pt;
      color: #666;
      white-space: nowrap;
      font-family: 'Arial', sans-serif;
    }

    /* ── Certifications ─────────────────────────────────── */
    .cert-list {
      list-style-type: disc;
      padding-left: 20px;
    }

    .cert-list li {
      font-size: 10pt;
      color: #333;
      line-height: 1.6;
      margin-bottom: 2px;
    }

    /* ── Print ──────────────────────────────────────────── */
    @media print {
      body, html { 
        background: white; 
        padding: 0; 
        margin: 0;
        font-size: 10pt; 
        height: auto !important; 
        overflow: visible !important;
      }
      .resume-wrapper { 
        box-shadow: none; 
        padding: 0; 
        margin: 0; 
        border-radius: 0; 
        max-width: none; 
        width: 100%;
      }
      .section { 
        page-break-inside: auto; 
      }
      .job { 
        page-break-inside: avoid; 
      }
      .edu-item { 
        page-break-inside: avoid; 
      }
      .cert-list {
        page-break-inside: auto;
      }
    }
  </style>
</head>
<body>
  <div class="resume-wrapper">

    <!-- ── Contact Header ────────────────────────────────── -->
    {% if contact %}
    <div class="header">
      {% if contact.name %}
      <div class="candidate-name">{{ contact.name }}</div>
      {% endif %}
      <div class="contact-bar">
        {% if contact.email %}
        <a href="mailto:{{ contact.email }}">{{ contact.email }}</a>
        {% endif %}
        {% if contact.phone %}
        <span class="contact-sep">|</span>
        <span>{{ contact.phone }}</span>
        {% endif %}
        {% if contact.location %}
        <span class="contact-sep">|</span>
        <span>{{ contact.location }}</span>
        {% endif %}
        {% if contact.linkedin %}
        <span class="contact-sep">|</span>
        <a href="{{ contact.linkedin }}" target="_blank">{{ contact.linkedin }}</a>
        {% endif %}
      </div>
    </div>
    {% endif %}

    <!-- ── Professional Summary ──────────────────────────── -->
    {% if summary %}
    <div class="section">
      <div class="section-title">Professional Summary</div>
      <p class="summary-text">{{ summary }}</p>
    </div>
    {% endif %}

    <!-- ── Skills ───────────────────────────────────────── -->
    {% if skills %}
    <div class="section">
      <div class="section-title">Technical Skills</div>
      <ul class="skills-grid">
        {% for skill in skills %}
        <li class="skill-tag">{{ skill }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    <!-- ── Professional Experience ──────────────────────── -->
    {% if experience %}
    <div class="section">
      <div class="section-title">Professional Experience</div>
      {% for job in experience %}
      <div class="job">
        <div class="job-header">
          <div class="job-title-company">
            {% if job.entry_type is defined and job.entry_type == 'project' %}
            <span class="job-title">{{ job.title | default('') }}</span>
            &nbsp;&mdash;&nbsp;<span class="job-company" style="font-style: normal; color: #1a365d; font-weight: 500;">Project</span>
            {% elif job.entry_type is defined and job.entry_type == 'volunteer' %}
            <span class="job-title">{{ job.title | default('') }}</span>
            {% if job.company %}
            &nbsp;&mdash;&nbsp;<span class="job-company">{{ job.company }}</span>
            {% else %}
            &nbsp;&mdash;&nbsp;<span class="job-company" style="font-style: normal; color: #1a365d; font-weight: 500;">Volunteer</span>
            {% endif %}
            {% else %}
            <span class="job-title">{{ job.title | default('') }}</span>
            {% if job.company %}
            &nbsp;&mdash;&nbsp;<span class="job-company">{{ job.company }}</span>
            {% endif %}
            {% endif %}
          </div>
          {% if job.dates %}
          <span class="job-dates">{{ job.dates }}</span>
          {% endif %}
        </div>
        {% if job.bullets %}
        <ul class="job-bullets">
          {% for bullet in job.bullets %}
          <li>{{ bullet }}</li>
          {% endfor %}
        </ul>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- ── Education ────────────────────────────────────── -->
    {% if education %}
    <div class="section">
      <div class="section-title">Education</div>
      {% for edu in education %}
      <div class="edu-item">
        <div>
          <div class="edu-degree">{{ edu.degree | default('') }}</div>
          {% if edu.institution %}
          <div class="edu-institution">{{ edu.institution }}</div>
          {% endif %}
        </div>
        {% if edu.year %}
        <span class="edu-year">{{ edu.year }}</span>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- ── Certifications ───────────────────────────────── -->
    {% if certifications and certifications | length > 0 %}
    <div class="section">
      <div class="section-title">Certifications</div>
      <ul class="cert-list">
        {% for cert in certifications %}
        <li>{{ cert }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

  </div><!-- /.resume-wrapper -->
</body>
</html>
```

Projects render with "— Project" suffix; volunteers with "— Volunteer". Standard jobs render as before. No empty company fields for non-job entries.

---

### 6. Test Fixture + Integration Tests
- **New:** [multi_page_resume.txt](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizer/tests/fixtures/multi_page_resume.txt) — 7-entry, 2-page resume with "SELECTED PROJECTS" and "VOLUNTEER EXPERIENCE" headers
- **New:** [test_parser_anti_truncation.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizer/tests/test_parser_anti_truncation.py) — 13 tests covering all fix aspects

## Testing

```
$ python -m pytest resume_optimizer/tests/test_parser_anti_truncation.py -v
============================= 13 passed in 0.08s ==============================
```

| Test Class | Tests | Status |
|---|---|---|
| TestPageBoundaryMarkers | 2 | ✅ All passed |
| TestExperienceCountPreservation | 2 | ✅ All passed |
| TestHeaderSynonymMapping | 2 | ✅ All passed |
| TestEntryTypeDiscriminator | 3 | ✅ All passed |
| TestAntiTruncationDirective | 2 | ✅ All passed |
| TestRewriterAssertionGuards | 2 | ✅ All passed |

## Files Changed Summary

| File | Change Type |
|---|---|
| `sub_agents/document_parser/agent.py` | Modified (prompt rewrite) |
| `sub_agents/document_parser/tools.py` | Modified (page markers) |
| `shared/state.py` | Modified (schema docs) |
| `sub_agents/resume_rewriter/agent.py` | Modified (schema + prompt + assertion) |
| `sub_agents/html_renderer/templates/resume.html` | Modified (entry_type rendering) |
| `tests/__init__.py` | New |
| `tests/fixtures/multi_page_resume.txt` | New |
| `tests/test_parser_anti_truncation.py` | New |

## Next Steps
- Run the full pipeline end-to-end with the multi-page fixture via `positive_test_scenario_api.py`
- Consider migrating DocumentParserAgent to structured output via `response_schema` (deferred per plan Q2)
