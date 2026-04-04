"""
ATS Pre-Check Agent (Agent 4 of 9) - Deterministic

Detects ATS-unfriendly formatting issues and calculates the
BEFORE ATS keyword match score as a baseline.
"""

from ...shared.python_task_node import PythonTaskNode
from ...shared.utils import get_dict_from_state
from .tools import detect_ats_unfriendly_formatting, calculate_ats_score

def run_ats_precheck(state: dict) -> dict:
    doc_out = get_dict_from_state(state.get("document_parser_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))
    
    raw_text = state.get("raw_resume_text", "")
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
