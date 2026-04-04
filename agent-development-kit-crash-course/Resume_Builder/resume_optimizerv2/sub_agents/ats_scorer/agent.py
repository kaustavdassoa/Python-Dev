"""
ATS Scorer Agent — AFTER (Agent 6 of 9) - Deterministic

Re-scores the rewritten resume against JD keywords to measure
improvement and calculate the delta from the baseline score.
"""

from ...shared.python_task_node import PythonTaskNode
from ...shared.utils import get_dict_from_state
from .tools import calculate_ats_score_after

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
