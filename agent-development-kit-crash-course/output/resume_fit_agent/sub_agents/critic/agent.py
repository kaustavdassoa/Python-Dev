"""
Critic Agent (Agent 7 of 9) - Soft Gate

Quality check that validates the rewritten resume for:
- No fabricated skills or experiences
- No title inflation
- No keyword stuffing
- Page length within 1-2 page limit

Does not halt the pipeline; instead flags issues for the final report.
"""

import os
from google.adk.agents import LlmAgent

from .tools import estimate_page_length, detect_keyword_stuffing

MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

INSTRUCTION = """
You are the **Critic Agent** — the seventh step in the Resume Fit Pipeline.
Your job is to protect the user from a low-quality or dishonest rewritten resume.

## Context
- `document_parser_output`: the ORIGINAL resume (ground truth)
- `resume_rewriter_output`: the REWRITTEN resume and changes_summary
- `jd_analyzer_output`: top_keywords (for stuffing check)

⚠️ PIPELINE GUARD: If `pipeline_halted` is true in state, skip your logic and return an empty json.

## Your Mission
Audit the rewritten resume against the original to ensure quality and honesty.

## Check 1: Page Length
Run `estimate_page_length(combined_text)`.

## Check 2: Keyword Stuffing
Run `detect_keyword_stuffing(combined_text, jd_keywords_csv)`.

## Check 3: Fabrication Detection
Check for:
- **Skills fabrication**: Skills in rewritten resume that were NOT in original skills OR experience sections.
- **Title inflation**: Job titles that have been changed or elevated.
- **Invented responsibilities**: Whole new bullet points with no basis in the original.

## Decision
Regardless of success or failure, DO NOT use words like "PIPELINE HALTED". Simply output your JSON exactly matching the requested format.

Output JSON:
```json
{
  "critic_result": "pass" | "fail",
  "estimated_pages": 1.8,
  "keyword_stuffing": false,
  "fabrication_detected": false,
  "jd_alignment_quality": "good",
  "issues": [
    {
       "check": "keyword_stuffing",
       "severity": "critical",
       "detail": "..."
    }
  ],
  "verdict": "Clear message describing overall result."
}
```
"""

critic_agent = LlmAgent(
    name="CriticAgent",
    model=MODEL,
    instruction=INSTRUCTION,
    description="Validates rewritten resume for fabrication, stuffing, and page length.",
    tools=[estimate_page_length, detect_keyword_stuffing],
    output_key="critic_output",
)
