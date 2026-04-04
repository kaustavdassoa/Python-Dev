"""
Alignment Validator Agent (Agent 3 of 9) — HARD GATE

Validates that the candidate's career level is reasonably aligned
with the job description's requirements. Refuses to proceed if the
gap is too large to bridge with resume rewording alone.

Converted to purely deterministic PythonTaskNode (Part 3 of FinOps Audit).
"""

from ...shared.python_task_node import PythonTaskNode
from ...shared.utils import get_dict_from_state
from .tools import compare_seniority_levels, check_domain_alignment, SENIORITY_LADDER
import logging

logger = logging.getLogger("AlignmentValidator")

class AbortPipelineError(Exception):
    pass

def infer_seniority_from_experience(experience_list: list) -> str:
    """Scan experience titles against SENIORITY_LADDER and pick highest match."""
    max_score = -1
    best_level = "entry"
    for exp in experience_list:
        title = exp.get("title", "").lower()
        if not title:
            continue
        for level, score in SENIORITY_LADDER.items():
            if level in title:
                if score > max_score:
                    max_score = score
                    best_level = level
    return best_level

def run_alignment_validator(state: dict) -> dict:
    doc_out = get_dict_from_state(state.get("document_parser_output", {}))
    jd_out = get_dict_from_state(state.get("jd_analyzer_output", {}))
    
    # Extract candidate data
    resume_sections = doc_out.get("resume_sections", {})
    experience = resume_sections.get("experience", [])
    skills_list = resume_sections.get("skills", [])
    resume_skills_csv = ",".join(skills_list)
    
    candidate_level = infer_seniority_from_experience(experience)
    
    # Extract JD data
    jd_level = jd_out.get("seniority_level", "mid")
    jd_level_score = jd_out.get("level_score", None)
    jd_required_skills = jd_out.get("required_skills", [])
    jd_required_skills_csv = ",".join(jd_required_skills)
    
    # Run deterministic tools
    seniority_result = compare_seniority_levels(candidate_level, jd_level, jd_score_override=jd_level_score)
    domain_result = check_domain_alignment(resume_skills_csv, jd_required_skills_csv)
    
    is_acceptable = seniority_result["is_acceptable"] and domain_result["is_domain_match"]
    
    result = {
        "alignment_result": "pass" if is_acceptable else "reject",
        "candidate_level": candidate_level,
        "candidate_label": seniority_result.get("candidate_label", ""),
        "jd_level": jd_level,
        "jd_label": seniority_result.get("jd_label", ""),
        "seniority_gap": seniority_result.get("gap", 0),
        "domain_overlap_pct": domain_result.get("overlap_pct", 0.0),
        "matched_skills": domain_result.get("matched_skills", []),
    }
    
    if not is_acceptable:
        reasons = []
        if not seniority_result["is_acceptable"]:
            reasons.append("seniority_gap_too_large")
        if not domain_result["is_domain_match"]:
            reasons.append("low_domain_overlap")
        reason = ", ".join(reasons)
        result["rejection_reason"] = reason
        raise AbortPipelineError(f"Alignment check failed: {reason}. Candidate level: {candidate_level}. JD level: {jd_level}. Domain overlap: {domain_result.get('overlap_pct', 0.0)}%")
        
    result["verdict"] = "Resume is alignable with the job description."
    return result

alignment_validator_agent = PythonTaskNode(
    name="AlignmentValidatorAgent",
    task_func=run_alignment_validator,
    output_key="alignment_validator_output",
    description="HARD GATE: deterministically validates career-level and domain alignment between resume and JD."
)
