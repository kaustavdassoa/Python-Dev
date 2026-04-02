"""
ATS Scorer Tools (AFTER rewriting)

Recalculates ATS keyword score after the resume has been rewritten.
"""


def calculate_ats_score_after(rewritten_text: str, jd_keywords_csv: str) -> dict:
    """
    Calculate ATS keyword match score AFTER resume rewriting.

    Args:
        rewritten_text: The full text of the rewritten resume sections combined.
        jd_keywords_csv: Comma-separated list of JD keywords.

    Returns:
        dict with: score_after (int 0-100), matched_keywords (list),
                   still_missing_keywords (list), total_jd_keywords (int)
    """
    jd_keywords = [k.strip().lower() for k in jd_keywords_csv.split(",") if k.strip()]
    if not jd_keywords:
        return {
            "score_after": 0,
            "matched_keywords": [],
            "still_missing_keywords": [],
            "total_jd_keywords": 0,
        }

    text_lower = rewritten_text.lower()
    matched = [kw for kw in jd_keywords if kw in text_lower]
    still_missing = [kw for kw in jd_keywords if kw not in text_lower]

    score = int((len(matched) / len(jd_keywords)) * 100)

    return {
        "score_after": score,
        "matched_keywords": matched,
        "still_missing_keywords": still_missing,
        "total_jd_keywords": len(jd_keywords),
    }
