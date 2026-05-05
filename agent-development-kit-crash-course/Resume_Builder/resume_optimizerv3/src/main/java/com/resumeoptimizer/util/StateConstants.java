package com.resumeoptimizer.util;

/**
 * Canonical session state key constants used across the pipeline.
 * Mirrors shared/state.py from the Python codebase.
 */
public final class StateConstants {

    private StateConstants() {}

    // ── Input Keys ──────────────────────────────────────────────────
    public static final String RAW_RESUME_TEXT = "raw_resume_text";
    public static final String RAW_JD_TEXT = "raw_jd_text";

    // ── Agent Output Keys ───────────────────────────────────────────
    public static final String DOCUMENT_PARSER_OUTPUT = "document_parser_output";
    public static final String JD_ANALYZER_OUTPUT = "jd_analysis_output";
    public static final String ALIGNMENT_VALIDATOR_OUTPUT = "alignment_validator_output";
    public static final String ATS_PRECHECK_OUTPUT = "ats_precheck_output";
    public static final String REWRITER_OUTPUT = "rewriter_output";
    public static final String ATS_SCORER_OUTPUT = "ats_scorer_output";
    public static final String CRITIC_OUTPUT = "critic_output";
    public static final String HTML_RENDERER_OUTPUT = "html_renderer_output";
    public static final String FINAL_REPORT = "final_report";

    // ── Pipeline Control Flags ──────────────────────────────────────
    public static final String PIPELINE_HALTED = "pipeline_halted";
    public static final String HALT_REASON = "halt_reason";
}
