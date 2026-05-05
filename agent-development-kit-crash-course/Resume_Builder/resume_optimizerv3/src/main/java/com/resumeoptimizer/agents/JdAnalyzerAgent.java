package com.resumeoptimizer.agents;

import com.google.adk.agents.LlmAgent;
import com.google.adk.tools.FunctionTool;
import com.resumeoptimizer.tools.JdAnalyzerTools;

/**
 * Agent 2 of 9 — JD Analyzer (LlmAgent + FunctionTools).
 * Analyzes the job description using deterministic regex tools,
 * with the LLM synthesizing results into structured output.
 */
public final class JdAnalyzerAgent {

    private JdAnalyzerAgent() {}

    public static LlmAgent create() {
        return LlmAgent.builder()
                .name("JdAnalyzerAgent")
                .model("gemini-2.0-flash")
                .instruction("""
                    You are a Job Description Analyzer. Use the provided tools to analyze the JD text
                    from the session state (key: raw_jd_text).
                    
                    Execute these steps IN ORDER:
                    1. Call checkJdAuthenticity with the JD text
                    2. Call extractSenioritySignals with the JD text
                    3. Call extractAtsKeywords with the JD text
                    4. Call extractJobMetadata with the JD text
                    
                    Then synthesize ALL tool results into a single JSON with these keys:
                    - is_authentic: boolean
                    - job_title: extracted job title from the JD text
                    - seniority_level: detected level string
                    - level_score: integer score from the ladder
                    - top_keywords: list of ATS keywords found
                    - required_skills: list of required skills from the JD
                    - preferred_skills: list of preferred/nice-to-have skills
                    - employment_type: full-time/contract/part-time/internship
                    - work_model: remote/hybrid/on-site/unspecified
                    - core_responsibilities: list of key responsibilities
                    
                    Return ONLY the JSON. Do not add commentary.
                    """)
                .description("Analyzes job description for seniority, keywords, and metadata.")
                .tools(
                    FunctionTool.create(JdAnalyzerTools.class, "checkJdAuthenticity"),
                    FunctionTool.create(JdAnalyzerTools.class, "extractSenioritySignals"),
                    FunctionTool.create(JdAnalyzerTools.class, "extractAtsKeywords"),
                    FunctionTool.create(JdAnalyzerTools.class, "extractJobMetadata")
                )
                .outputKey("jd_analysis_output")
                .disallowTransferToParent(true)
                .disallowTransferToPeers(true)
                .build();
    }
}
