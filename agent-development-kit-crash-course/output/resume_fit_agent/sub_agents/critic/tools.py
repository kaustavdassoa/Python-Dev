"""
Critic Agent Tools

Checks page length estimate and keyword stuffing after rewriting.
"""

import re


def estimate_page_length(rewritten_resume_text: str) -> dict:
    """
    Estimate the number of printed pages based on word count.
    Rule of thumb: ~400 words ≈ 1 page.

    Args:
        rewritten_resume_text: The full text of the rewritten resume.

    Returns:
        dict with: word_count (int), estimated_pages (float),
                   status ("ok" | "too_short" | "too_long"), message (str)
    """
    word_count = len(rewritten_resume_text.split())
    estimated_pages = round(word_count / 400, 1)

    if estimated_pages < 0.4:
        status = "too_short"
        message = f"Estimated {estimated_pages} pages ({word_count} words). Resume may be too brief."
    elif estimated_pages > 2.3:
        status = "too_long"
        message = f"Estimated {estimated_pages} pages ({word_count} words). Resume exceeds 2-page limit — please trim."
    else:
        status = "ok"
        message = f"Estimated {estimated_pages} pages ({word_count} words). Within 1–2 page target. ✅"

    return {
        "word_count": word_count,
        "estimated_pages": estimated_pages,
        "status": status,
        "message": message,
    }


def detect_keyword_stuffing(rewritten_resume_text: str, jd_keywords_csv: str) -> dict:
    """
    Detect if any JD keyword appears unnaturally many times in the rewritten resume.
    Threshold: > 4 occurrences = stuffed.

    Args:
        rewritten_resume_text: Full text of the rewritten resume.
        jd_keywords_csv: Comma-separated list of JD keywords.

    Returns:
        dict with: has_stuffing (bool), stuffed_keywords (list of {keyword, count})
    """
    keywords = [k.strip().lower() for k in jd_keywords_csv.split(",") if k.strip()]
    text_lower = rewritten_resume_text.lower()

    stuffed = []
    for keyword in keywords:
        count = len(re.findall(r"\b" + re.escape(keyword) + r"\b", text_lower))
        if count > 4:
            stuffed.append({"keyword": keyword, "count": count})

    return {
        "has_stuffing": len(stuffed) > 0,
        "stuffed_keywords": stuffed,
    }
