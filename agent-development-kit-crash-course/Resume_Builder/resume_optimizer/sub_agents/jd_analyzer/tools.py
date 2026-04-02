"""
JD Analyzer Tools

Rule-based helpers for JD authenticity check, seniority detection,
keyword extraction, and metadata parsing.
"""

import re


# ─── Seniority Ladder ────────────────────────────────────────────────────────
SENIORITY_LEVELS = {
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
    "cpo": 8,
}

# ─── Tech Keyword Patterns ───────────────────────────────────────────────────
TECH_PATTERNS = [
    # Languages
    r"\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Swift|Kotlin|Ruby|PHP|Scala|R|MATLAB)\b",
    # Cloud & DevOps
    r"\b(AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Terraform|Jenkins|CI/CD|GitLab|GitHub Actions|Ansible|Helm)\b",
    # Frameworks
    r"\b(React|Angular|Vue|Node\.js|Django|Flask|FastAPI|Spring|\.NET|Express|Next\.js|NestJS|Rails)\b",
    # Databases
    r"\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Cassandra|DynamoDB|BigQuery|Snowflake|Redshift)\b",
    # ML / AI
    r"\b(Machine Learning|Deep Learning|TensorFlow|PyTorch|scikit-learn|NLP|LLM|GenAI|AI|MLOps|Spark)\b",
    # Methodologies
    r"\b(Agile|Scrum|Kanban|DevOps|RESTful|GraphQL|Microservices|SOA|TDD|BDD|SOLID)\b",
    # Tools
    r"\b(Git|Jira|Confluence|Linux|Unix|Bash|PowerShell|Postman|Grafana|Prometheus|Datadog)\b",
    # Soft skills
    r"\b(leadership|communication|collaboration|problem.solving|analytical|critical thinking|mentoring)\b",
]


def check_jd_authenticity(jd_text: str) -> dict:
    """
    Rule-based check: does the text look like a real job description?

    Args:
        jd_text: The raw job description text.

    Returns:
        dict with: is_authentic (bool), confidence (float), word_count (int), reason (str)
    """
    word_count = len(jd_text.split())

    # Core JD section markers
    jd_markers = [
        r"\b(responsibilities|duties|what you.ll do|your role)\b",
        r"\b(requirements|qualifications|what we.re looking for|we are looking for)\b",
        r"\b(skills|experience|background|expertise)\b",
        r"\b(job description|about the role|about this role|position overview)\b",
        r"\b(engineer|developer|manager|analyst|designer|director|vp|lead|architect|specialist)\b",
    ]

    score = 0
    signals = []
    for pattern in jd_markers:
        if re.search(pattern, jd_text, re.IGNORECASE):
            score += 1
            signals.append(pattern)

    length_ok = word_count >= 50
    confidence = (score / len(jd_markers)) * 0.7 + (0.3 if length_ok else 0.0)
    is_authentic = confidence >= 0.35

    reason = (
        "Text appears to be a valid job description."
        if is_authentic
        else f"Text does not appear to be a job description. Only {score}/{len(jd_markers)} JD markers found and word count is {word_count}."
    )

    return {
        "is_authentic": is_authentic,
        "confidence": round(confidence, 2),
        "signals_found": len(signals),
        "word_count": word_count,
        "reason": reason,
    }


def extract_seniority_signals(jd_text: str) -> dict:
    """
    Extract seniority level from JD using keywords and years-of-experience patterns.

    Args:
        jd_text: The raw job description text.

    Returns:
        dict with: detected_level (str), level_score (int), signals_found (list), years_required (list)
    """
    # Extract years of experience
    years_pattern = re.findall(
        r"(\d+)\+?\s*(?:to\s*\d+)?\s*years?\s*(?:of\s+)?(?:experience|exp\.?)",
        jd_text,
        re.IGNORECASE,
    )
    years_list = [int(y) for y in years_pattern]

    detected_level = "mid"
    level_score = 2
    detected_signals = []

    for keyword, score in SENIORITY_LEVELS.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", jd_text, re.IGNORECASE):
            detected_signals.append(keyword)
            if score > level_score:
                level_score = score
                detected_level = keyword

    # Override with max years if found
    if years_list:
        max_years = max(years_list)
        if max_years >= 15:
            detected_level, level_score = "director", 6
        elif max_years >= 10:
            detected_level, level_score = "lead", 4
        elif max_years >= 5:
            detected_level, level_score = "senior", 3
        elif max_years >= 2:
            detected_level, level_score = "mid", 2
        else:
            detected_level, level_score = "junior", 1

    return {
        "detected_level": detected_level,
        "level_score": level_score,
        "signals_found": detected_signals,
        "years_required": years_list,
    }


def extract_ats_keywords(jd_text: str) -> dict:
    """
    Extract ATS-relevant keywords from JD using regex patterns.

    Args:
        jd_text: The raw job description text.

    Returns:
        dict with: keywords (list of str), total_found (int)
    """
    keywords = set()

    for pattern in TECH_PATTERNS:
        matches = re.findall(pattern, jd_text, re.IGNORECASE)
        keywords.update([m.strip() for m in matches if m.strip()])

    # Cap at top 30 unique keywords
    keyword_list = sorted(list(keywords))[:30]

    return {"keywords": keyword_list, "total_found": len(keyword_list)}


def extract_job_metadata(jd_text: str) -> dict:
    """
    Extract employment type and work model from JD.

    Args:
        jd_text: The raw job description text.

    Returns:
        dict with: employment_type (str), work_model (str)
    """
    # Employment type
    employment_type = "full-time"
    if re.search(r"\b(contract|contractor|freelance|1099)\b", jd_text, re.IGNORECASE):
        employment_type = "contract"
    elif re.search(r"\b(part.time|part time)\b", jd_text, re.IGNORECASE):
        employment_type = "part-time"
    elif re.search(r"\b(intern|internship)\b", jd_text, re.IGNORECASE):
        employment_type = "internship"

    # Work model
    work_model = "unspecified"
    if re.search(r"\b(remote|work from home|wfh)\b", jd_text, re.IGNORECASE):
        work_model = "remote"
    elif re.search(r"\b(hybrid)\b", jd_text, re.IGNORECASE):
        work_model = "hybrid"
    elif re.search(r"\b(on.site|onsite|in.office)\b", jd_text, re.IGNORECASE):
        work_model = "on-site"

    return {"employment_type": employment_type, "work_model": work_model}
