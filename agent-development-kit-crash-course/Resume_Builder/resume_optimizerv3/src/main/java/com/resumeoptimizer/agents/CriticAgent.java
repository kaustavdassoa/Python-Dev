package com.resumeoptimizer.agents;

import com.google.adk.agents.Instruction;
import com.google.adk.agents.LlmAgent;
import com.google.adk.agents.ReadonlyContext;
import com.google.adk.tools.FunctionTool;
import com.resumeoptimizer.tools.CriticTools;
import io.reactivex.rxjava3.core.Single;

/**
 * Agent 7 of 9 — Critic (LlmAgent + FunctionTools).
 * Quality check: page length, keyword stuffing (deterministic tools),
 * and fabrication detection (LLM call — visible in ADK Dev UI).
 */
public final class CriticAgent {

    private CriticAgent() {}

    public static LlmAgent create() {
        Instruction.Provider instructionProvider = new Instruction.Provider((ReadonlyContext ctx) -> {
            String docOutput = String.valueOf(ctx.state().get("document_parser_output"));
            String rewriterOutput = String.valueOf(ctx.state().get("rewriter_output"));
            String jdOutput = String.valueOf(ctx.state().get("jd_analysis_output"));

            return Single.just(String.format("""
                You are a Resume Quality Critic. Validate the rewritten resume for quality issues.

                STEPS:
                1. Call estimatePageLength with the full rewritten resume text (JSON stringified)
                2. Call detectKeywordStuffing with the resume text and JD keywords
                3. Perform fabrication detection yourself by comparing original vs rewritten:
                   - Check for skills that exist in the rewrite but NOT in the original
                   - Check for title inflation (e.g., "Developer" → "Senior Developer")

                Return a JSON with:
                - critic_result: "pass" or "fail"
                - estimated_pages: number from page length tool
                - keyword_stuffing: boolean from stuffing tool
                - fabrication_detected: boolean
                - jd_alignment_quality: "good" or "poor"
                - issues: list of {check, severity, detail}
                - verdict: summary string

                Severity levels: "critical" (fail) or "warning" (pass with note)

                === ORIGINAL RESUME ===
                %s

                === REWRITTEN RESUME ===
                %s

                === JD ANALYSIS ===
                %s
                """, docOutput, rewriterOutput, jdOutput));
        });

        return LlmAgent.builder()
                .name("CriticAgent")
                .model("gemini-2.0-flash")
                .instruction(instructionProvider)
                .tools(
                    FunctionTool.create(CriticTools.class, "estimatePageLength"),
                    FunctionTool.create(CriticTools.class, "detectKeywordStuffing")
                )
                .outputKey("critic_output")
                .disallowTransferToParent(true)
                .disallowTransferToPeers(true)
                .build();
    }
}
