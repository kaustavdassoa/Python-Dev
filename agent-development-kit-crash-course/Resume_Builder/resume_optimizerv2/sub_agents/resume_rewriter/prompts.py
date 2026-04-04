"""
Resume Rewriter Agent — Prompt Templates

Contains the prompt template constants used by the rewriter's map-reduce loop.
Separated from agent.py for clean code organization and independent prompt iteration.
"""

BASE_REWRITE_PROMPT = """
Rewrite the summary and skills sections of this resume to maximize ATS fit.
Context:
{context}

Original Summary:
{summary}

Original Skills:
{skills}

Rules:
1. Never fabricate skills not in the original.
2. Natural keyword injection only.
"""

EXPERIENCE_REWRITE_PROMPT = """
Rewrite the following single experience entry to maximize ATS fit.
Context:
{context}

Rules:
1. Never fabricate dates, titles, or responsibilities.
2. Upgrade weak verbs.
3. Replace special bullet characters with standard hyphens (-).
4. UNRELATED EXPERIENCE SAFEGUARD: Do not force technical keywords into unrelated roles.
5. PROJECT ENTRY SAFEGUARD: If entry_type is "project", preserve the project framing.
6. Preserve the entry_type field exactly as provided in the original.

[CACHE BOUNDARY]

Original Experience:
{exp}
"""
