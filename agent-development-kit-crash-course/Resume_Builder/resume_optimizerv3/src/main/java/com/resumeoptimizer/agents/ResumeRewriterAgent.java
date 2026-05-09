package com.resumeoptimizer.agents;

import com.google.adk.agents.Instruction;
import com.google.adk.agents.LlmAgent;
import com.google.adk.agents.ReadonlyContext;
import com.resumeoptimizer.util.SchemaUtil;
import com.resumeoptimizer.model.RewriterResult;
import io.reactivex.rxjava3.core.Single;

/**
 * Agent 5 of 9 — Resume Rewriter (LlmAgent — Path A: Single-Shot Generation).
 *
 * Uses Gemini 2.0 Flash's 1M+ token context window to rewrite the entire resume
 * in a single pass. No map-reduce loop, no tools, no rate limiting.
 *
 * Uses Instruction.Provider to inject session state and avoid literal brace conflicts.
 */
public final class ResumeRewriterAgent {

    private ResumeRewriterAgent() {}

    public static LlmAgent create(String modelName) {
        Instruction.Provider instructionProvider = new Instruction.Provider((ReadonlyContext ctx) -> {
            String parsedResume = String.valueOf(ctx.state().get("document_parser_output"));
            String jdAnalysis = String.valueOf(ctx.state().get("jd_analysis_output"));
            String precheck = String.valueOf(ctx.state().get("ats_precheck_output"));

            return Single.just(String.format("""
                You are an expert Resume Rewriter. Your task is to rewrite the ENTIRE resume
                to perfectly align with the provided Job Description.

                RULES:
                - Apply the XYZ formula (Accomplished X, as measured by Y, by doing Z) to ALL bullet points
                - Naturally integrate missing keywords from the Gap Report into appropriate sections
                - Preserve ALL factual data: dates, company names, institutions, degrees
                - Keep the SAME number of experience entries — do NOT add or remove entries
                - Do NOT fabricate skills, certifications, or experiences
                - Do NOT inflate job titles
                - Maintain the entry_type field for each experience (job, project, volunteer)
                - Include a changes_summary list documenting what was changed
                - Include a keywords_injected list of keywords that were added
                - Return the COMPLETE rewritten resume matching the required JSON schema

                === ORIGINAL PARSED RESUME ===
                %s

                === JOB DESCRIPTION ANALYSIS ===
                %s

                === ATS PRE-CHECK (GAP REPORT) ===
                %s
                """, parsedResume, jdAnalysis, precheck));
        });

        return LlmAgent.builder()
                .name("ResumeRewriterAgent")
                .model(modelName)
                .instruction(instructionProvider)
                .outputKey("rewriter_output")
                .disallowTransferToParent(true)
                .disallowTransferToPeers(true)
                .build();
    }
}
