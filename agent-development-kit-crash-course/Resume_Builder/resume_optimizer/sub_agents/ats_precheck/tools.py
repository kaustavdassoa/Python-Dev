"""
ATS Pre-Check Tools

Detects ATS-unfriendly formatting issues and calculates BEFORE keyword score.
"""

import re


def detect_ats_unfriendly_formatting(resume_text: str) -> dict:
    """
    Scan resume text for ATS-unfriendly formatting patterns.

    Args:
        resume_text: Raw extracted resume text.

    Returns:
        dict with: has_warnings (bool), warning_count (int), critical_count (int),
                   warnings (list of {type, severity, message})
    """
    warnings = []

    # 1. Multi-column layout (excessive tabs / aligned whitespace)
    tab_count = len(re.findall(r"\t{2,}|\s{6,}", resume_text))
    if tab_count > 5:
        warnings.append(
            {
                "type": "multi_column",
                "severity": "critical",
                "message": (
                    "Possible multi-column layout detected (excessive tabs/spaces). "
                    "Many ATS parsers read only the left column and lose right-side content."
                ),
            }
        )

    # 2. Table-like structures (pipe characters)
    if re.search(r"\|.{3,}\|", resume_text):
        warnings.append(
            {
                "type": "table",
                "severity": "critical",
                "message": (
                    "Table structure detected (pipe characters). "
                    "ATS systems typically cannot parse table cells correctly."
                ),
            }
        )

    # 3. Special / non-ASCII bullet characters
    special_chars = re.findall(r"[•◦▪▸►→■□✓✗✦★☆❖◆]", resume_text)
    if special_chars:
        unique_chars = list(set(special_chars))
        warnings.append(
            {
                "type": "special_characters",
                "severity": "warning",
                "message": (
                    f"Special bullet/arrow characters found: {unique_chars}. "
                    "Replace with standard hyphens (-) or asterisks (*) for better ATS compatibility."
                ),
            }
        )

    # 4. Possible repeated header/footer
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line) > 3 and resume_text.count(first_line) > 1:
            warnings.append(
                {
                    "type": "repeated_header",
                    "severity": "warning",
                    "message": (
                        f'First line "{first_line[:40]}..." appears more than once. '
                        "This may indicate a repeated header/footer that confuses ATS parsers."
                    ),
                }
            )

    # 5. Very short text (likely parsing failure)
    word_count = len(resume_text.split())
    if word_count < 100:
        warnings.append(
            {
                "type": "insufficient_content",
                "severity": "critical",
                "message": (
                    f"Only {word_count} words extracted. "
                    "This may indicate a parsing failure (e.g., image-based PDF). "
                    "Please provide a text-based file."
                ),
            }
        )

    critical_count = sum(1 for w in warnings if w["severity"] == "critical")

    return {
        "has_warnings": len(warnings) > 0,
        "warning_count": len(warnings),
        "critical_count": critical_count,
        "warnings": warnings,
    }


def calculate_ats_score(resume_text: str, jd_keywords_csv: str) -> dict:
    """
    Calculate ATS keyword match score (BEFORE rewriting).

    Args:
        resume_text: Raw extracted resume text.
        jd_keywords_csv: Comma-separated list of JD keywords.

    Returns:
        dict with: score (int 0-100), matched_keywords (list), missing_keywords (list),
                   total_jd_keywords (int)
    """
    jd_keywords = [k.strip().lower() for k in jd_keywords_csv.split(",") if k.strip()]
    if not jd_keywords:
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "total_jd_keywords": 0,
        }

    resume_lower = resume_text.lower()
    matched = [kw for kw in jd_keywords if kw in resume_lower]
    missing = [kw for kw in jd_keywords if kw not in resume_lower]

    score = int((len(matched) / len(jd_keywords)) * 100)

    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "total_jd_keywords": len(jd_keywords),
    }
