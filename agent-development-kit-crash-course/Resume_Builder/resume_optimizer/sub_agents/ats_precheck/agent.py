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
