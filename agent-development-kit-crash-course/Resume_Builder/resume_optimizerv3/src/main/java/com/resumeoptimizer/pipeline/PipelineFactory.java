package com.resumeoptimizer.pipeline;

import com.google.adk.agents.SequentialAgent;
import com.resumeoptimizer.agents.*;

/**
 * Builds the root SequentialAgent pipeline — 9 agents in order.
 * Mirrors Python's agent.py root_agent definition.
 */
public final class PipelineFactory {

    private PipelineFactory() {}

    /**
     * Create the full 9-agent sequential pipeline.
     *
     * Agents 1-2: LlmAgent (Document Parser, JD Analyzer)
     * Agent 3: DeterministicAgent — HARD GATE (Alignment Validator)
     * Agent 4: DeterministicAgent (ATS Pre-Check)
     * Agent 5: LlmAgent — Path A (Resume Rewriter)
     * Agent 6: DeterministicAgent (ATS Scorer)
     * Agent 7: LlmAgent (Critic)
     * Agent 8: DeterministicAgent (HTML Renderer)
     * Agent 9: DeterministicAgent (Report Generator)
     */
    public static SequentialAgent createPipeline(String modelName) {
        return SequentialAgent.builder()
                .name("ResumeOptimizerPipeline")
                .description("9-agent sequential resume optimization pipeline built with Google ADK Java")
                .subAgents(
                        DocumentParserAgent.create(modelName),       // Agent 1
                        JdAnalyzerAgent.create(modelName),            // Agent 2
                        AlignmentValidatorAgent.create(),    // Agent 3 — HARD GATE
                        AtsPreCheckAgent.create(),           // Agent 4
                        ResumeRewriterAgent.create(modelName),        // Agent 5 — Path A
                        AtsScorerAgent.create(),             // Agent 6
                        CriticAgent.create(modelName),                // Agent 7
                        HtmlRendererAgent.create(),          // Agent 8
                        ReportGeneratorAgent.create()        // Agent 9
                )
                .build();
    }
}
