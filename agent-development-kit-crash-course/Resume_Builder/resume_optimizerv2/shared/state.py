"""
Shared session state schema for the Resume Optimizer pipeline.

All agents read from and write to ADK session state using these constants.
The state is passed in-memory through the SequentialAgent pipeline.
"""

# ── Stage 1: Document Parser ──────────────────────────────────────────────────
DOCUMENT_PARSER_OUTPUT = "document_parser_output"
# JSON: { completeness_status, missing_sections, experience_entry_count,
#         resume_sections: { contact, summary, skills,
#             experience: [{ title, company, dates, bullets, entry_type }],
#             education, certifications } }
# entry_type values: "job", "project", "volunteer", "other"
# NOTE: raw_text is NOT in this output; use state["raw_resume_text"] instead.

# ── Stage 2: JD Analyzer ─────────────────────────────────────────────────────
JD_ANALYZER_OUTPUT = "jd_analyzer_output"
# JSON: { authenticity_status, job_title, seniority_level, required_skills,
#         preferred_skills, top_keywords, responsibilities, employment_type }

# ── Stage 3: Alignment Validator ─────────────────────────────────────────────
ALIGNMENT_VALIDATOR_OUTPUT = "alignment_validator_output"
# JSON: { alignment_result, candidate_level, jd_level, seniority_gap,
#         domain_overlap_pct, rejection_message }

# ── Stage 4: ATS Pre-Check ───────────────────────────────────────────────────
ATS_PRECHECK_OUTPUT = "ats_precheck_output"
# JSON: { formatting_warnings, ats_score_before, matched_keywords_before,
#         missing_keywords }

# ── Stage 5: Resume Rewriter ─────────────────────────────────────────────────
RESUME_REWRITER_OUTPUT = "resume_rewriter_output"
# JSON: { rewritten_resume: { contact, summary, skills, experience, education,
#         certifications }, changes_summary }

# ── Stage 6: ATS Scorer (After) ──────────────────────────────────────────────
ATS_SCORER_OUTPUT = "ats_scorer_output"
# JSON: { ats_score_after, score_delta, still_missing_keywords,
#         matched_keywords_after }

# ── Stage 7: Critic ──────────────────────────────────────────────────────────
CRITIC_OUTPUT = "critic_output"
# JSON: { critic_result, issues, estimated_pages }

# ── Stage 8: HTML Renderer ───────────────────────────────────────────────────
HTML_RENDERER_OUTPUT = "html_renderer_output"
# String: complete self-contained HTML document

# ── Stage 9: Report Generator ────────────────────────────────────────────────
FINAL_REPORT = "final_report"
# String: formatted analysis report (markdown / plain text)

# ── Pipeline Control Signals ─────────────────────────────────────────────────
PIPELINE_HALTED = "pipeline_halted"
HALT_REASON = "halt_reason"
