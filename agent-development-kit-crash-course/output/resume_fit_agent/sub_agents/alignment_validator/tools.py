"""
Alignment Validator Tools

Rule-based seniority ladder comparison and domain overlap checker.
"""

import re

# ─── Seniority Ladder (ordinal scores) ──────────────────────────────────────
SENIORITY_LADDER: dict[str, int] = {
    "intern": 0,
    "internship": 0,
    "entry": 1,
    "entry-level": 1,
    "junior": 1,
    "jr": 1,
    "associate": 1,
    "mid": 2,
    "mid-level": 2,
    "intermediate": 2,
    "senior": 3,
    "sr": 3,
    "lead": 4,
    "principal": 5,
    "staff": 5,
    "architect": 5,
    "director": 6,
    "vp": 7,
    "vice president": 7,
    "c-suite": 8,
    "cto": 8,
    "ceo": 8,
}

LEVEL_LABELS = {
    0: "Intern",
    1: "Junior / Entry-Level",
    2: "Mid-Level",
    3: "Senior",
    4: "Lead",
    5: "Principal / Staff",
    6: "Director",
    7: "VP",
    8: "C-Suite",
}

# Maximum allowed seniority gap (in ladder steps)
MAX_GAP = 2


def compare_seniority_levels(candidate_level: str, jd_level: str) -> dict:
    """
    Compare candidate seniority to JD required seniority using the ladder.

    Args:
        candidate_level: Detected seniority of the candidate (from resume).
        jd_level: Required seniority from the job description.

    Returns:
        dict with: candidate_score, jd_score, gap, direction, is_acceptable, verdict,
                   candidate_label, jd_label
    """
    c_score = SENIORITY_LADDER.get(candidate_level.lower().strip(), 2)
    j_score = SENIORITY_LADDER.get(jd_level.lower().strip(), 2)

    gap = abs(j_score - c_score)
    direction = "match" if gap == 0 else ("under-qualified" if j_score > c_score else "over-qualified")
    is_acceptable = gap <= MAX_GAP

    return {
        "candidate_score": c_score,
        "jd_score": j_score,
        "candidate_label": LEVEL_LABELS.get(c_score, candidate_level),
        "jd_label": LEVEL_LABELS.get(j_score, jd_level),
        "gap": gap,
        "direction": direction,
        "is_acceptable": is_acceptable,
        "verdict": "aligned" if is_acceptable else "rejected",
    }


def check_domain_alignment(resume_skills: str, jd_required_skills: str) -> dict:
    """
    Check skill domain overlap between candidate resume and JD requirements.

    Args:
        resume_skills: Comma-separated list of skills from the resume.
        jd_required_skills: Comma-separated list of required skills from JD.

    Returns:
        dict with: overlap_count, overlap_pct, is_domain_match, matched_skills, unmatched_jd_skills
    """
    resume_list = [s.strip().lower() for s in resume_skills.split(",") if s.strip()]
    jd_list = [s.strip().lower() for s in jd_required_skills.split(",") if s.strip()]

    if not jd_list:
        return {
            "overlap_count": 0,
            "overlap_pct": 100.0,
            "is_domain_match": True,
            "matched_skills": [],
            "unmatched_jd_skills": [],
        }

    matched = []
    unmatched = []
    for jd_skill in jd_list:
        found = any(
            jd_skill in r_skill or r_skill in jd_skill
            for r_skill in resume_list
        )
        if found:
            matched.append(jd_skill)
        else:
            unmatched.append(jd_skill)

    overlap_pct = (len(matched) / len(jd_list)) * 100

    return {
        "overlap_count": len(matched),
        "overlap_pct": round(overlap_pct, 1),
        "is_domain_match": overlap_pct >= 15.0,  # At least 15% overlap to proceed
        "matched_skills": matched,
        "unmatched_jd_skills": unmatched,
    }
